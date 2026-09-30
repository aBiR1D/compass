"""SQLite-backed progress tracking and persistence."""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import aiosqlite

from compass.models import LifeMap, ProgressEntry, UserProfile

_DB_PATH = os.getenv("COMPASS_DB_PATH", str(Path.home() / ".compass" / "compass.db"))


def _ensure_dir() -> str:
    Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return _DB_PATH


async def _get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_ensure_dir())
    await db.execute("PRAGMA journal_mode=WAL")
    await _init_tables(db)
    return db


async def _init_tables(db: aiosqlite.Connection) -> None:
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            action_completed TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            mood_score INTEGER NOT NULL DEFAULT 5,
            energy_score INTEGER NOT NULL DEFAULT 5,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS life_maps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    await db.commit()


# ── Profile persistence ──────────────────────────────────────────────


async def save_profile(profile: UserProfile) -> int:
    """Persist a user profile and return its row id."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO profiles (data) VALUES (?)",
            (profile.model_dump_json(),),
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore[return-value]
    finally:
        await db.close()


async def load_profile() -> Optional[UserProfile]:
    """Load the most recent user profile, or ``None``."""
    db = await _get_db()
    try:
        cursor = await db.execute("SELECT data FROM profiles ORDER BY id DESC LIMIT 1")
        row = await cursor.fetchone()
        if row is None:
            return None
        return UserProfile.model_validate_json(row[0])
    finally:
        await db.close()


# ── Life-map persistence ─────────────────────────────────────────────


async def save_life_map(life_map: LifeMap) -> int:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO life_maps (data) VALUES (?)",
            (life_map.model_dump_json(),),
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore[return-value]
    finally:
        await db.close()


async def load_life_map() -> Optional[LifeMap]:
    db = await _get_db()
    try:
        cursor = await db.execute("SELECT data FROM life_maps ORDER BY id DESC LIMIT 1")
        row = await cursor.fetchone()
        if row is None:
            return None
        return LifeMap.model_validate_json(row[0])
    finally:
        await db.close()


# ── Progress tracking ─────────────────────────────────────────────────


async def log_progress(entry: ProgressEntry) -> int:
    """Save a daily progress entry. Returns the row id."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO progress (entry_date, action_completed, notes, mood_score, energy_score) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                entry.entry_date.isoformat(),
                entry.action_completed,
                entry.notes,
                entry.mood_score,
                entry.energy_score,
            ),
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore[return-value]
    finally:
        await db.close()


async def get_progress(since: date | None = None) -> list[ProgressEntry]:
    """Retrieve progress entries, optionally filtered by date."""
    db = await _get_db()
    try:
        if since:
            cursor = await db.execute(
                "SELECT entry_date, action_completed, notes, mood_score, energy_score "
                "FROM progress WHERE entry_date >= ? ORDER BY entry_date",
                (since.isoformat(),),
            )
        else:
            cursor = await db.execute(
                "SELECT entry_date, action_completed, notes, mood_score, energy_score "
                "FROM progress ORDER BY entry_date"
            )
        rows = await cursor.fetchall()
        return [
            ProgressEntry(
                entry_date=date.fromisoformat(r[0]),
                action_completed=r[1],
                notes=r[2],
                mood_score=r[3],
                energy_score=r[4],
            )
            for r in rows
        ]
    finally:
        await db.close()


async def get_streak() -> int:
    """Count consecutive days (up to today) with at least one logged action."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT DISTINCT entry_date FROM progress ORDER BY entry_date DESC"
        )
        rows = await cursor.fetchall()
        if not rows:
            return 0
        streak = 0
        expected = date.today()
        for (d_str,) in rows:
            d = date.fromisoformat(d_str)
            if d == expected:
                streak += 1
                expected -= timedelta(days=1)
            elif d < expected:
                break
        return streak
    finally:
        await db.close()


async def get_weekly_summary() -> dict:
    """Summarise this week's progress."""
    week_start = date.today() - timedelta(days=date.today().weekday())
    entries = await get_progress(since=week_start)
    if not entries:
        return {
            "days_logged": 0,
            "avg_mood": 0.0,
            "avg_energy": 0.0,
            "actions_completed": 0,
        }
    return {
        "days_logged": len({e.entry_date for e in entries}),
        "avg_mood": round(sum(e.mood_score for e in entries) / len(entries), 1),
        "avg_energy": round(sum(e.energy_score for e in entries) / len(entries), 1),
        "actions_completed": len(entries),
    }


async def get_life_score_trend() -> list[dict]:
    """Return chronologically ordered life-map snapshots with scores.

    Each element: ``{"date": "...", "scores": {...}}``
    """
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT data, created_at FROM life_maps ORDER BY created_at"
        )
        rows = await cursor.fetchall()
        trend: list[dict] = []
        for data_json, created_at in rows:
            lm = LifeMap.model_validate_json(data_json)
            scores = {
                ls.area.value: ls.current_score for ls in lm.profile.life_scores
            }
            trend.append({"date": created_at, "scores": scores})
        return trend
    finally:
        await db.close()
