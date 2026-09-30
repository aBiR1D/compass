"""Tests for the Compass tracker (SQLite persistence)."""

from __future__ import annotations

import os
import tempfile
from datetime import date, timedelta

import pytest

from compass.models import LifeArea, LifeMap, LifeScore, ProgressEntry, UserProfile

# Use a temporary database for tests
_tmp = tempfile.mkdtemp()
os.environ["COMPASS_DB_PATH"] = os.path.join(_tmp, "test_compass.db")

from compass import tracker  # noqa: E402 — must import after env override


@pytest.fixture(autouse=True)
async def _clean_db():
    """Reset the database between tests."""
    db = await tracker._get_db()
    await db.executescript(
        "DELETE FROM profiles; DELETE FROM progress; DELETE FROM life_maps;"
    )
    await db.commit()
    await db.close()
    yield


class TestProfilePersistence:
    async def test_save_and_load_profile(self) -> None:
        profile = UserProfile(name="Test User", age=30, profession="Engineer")
        row_id = await tracker.save_profile(profile)
        assert row_id is not None and row_id > 0

        loaded = await tracker.load_profile()
        assert loaded is not None
        assert loaded.name == "Test User"
        assert loaded.age == 30

    async def test_load_empty_returns_none(self) -> None:
        loaded = await tracker.load_profile()
        assert loaded is None

    async def test_latest_profile_wins(self) -> None:
        await tracker.save_profile(UserProfile(name="First"))
        await tracker.save_profile(UserProfile(name="Second"))
        loaded = await tracker.load_profile()
        assert loaded is not None
        assert loaded.name == "Second"


class TestProgressTracking:
    async def test_log_and_retrieve(self) -> None:
        entry = ProgressEntry(
            entry_date=date.today(),
            action_completed="Meditated",
            mood_score=8,
            energy_score=7,
        )
        row_id = await tracker.log_progress(entry)
        assert row_id > 0

        entries = await tracker.get_progress()
        assert len(entries) == 1
        assert entries[0].action_completed == "Meditated"
        assert entries[0].mood_score == 8

    async def test_filter_by_date(self) -> None:
        yesterday = date.today() - timedelta(days=1)
        await tracker.log_progress(
            ProgressEntry(entry_date=yesterday, action_completed="Old task")
        )
        await tracker.log_progress(
            ProgressEntry(entry_date=date.today(), action_completed="Today task")
        )

        all_entries = await tracker.get_progress()
        assert len(all_entries) == 2

        today_entries = await tracker.get_progress(since=date.today())
        assert len(today_entries) == 1
        assert today_entries[0].action_completed == "Today task"

    async def test_streak_zero_when_empty(self) -> None:
        streak = await tracker.get_streak()
        assert streak == 0

    async def test_streak_counts_consecutive_days(self) -> None:
        today = date.today()
        for i in range(3):
            await tracker.log_progress(
                ProgressEntry(entry_date=today - timedelta(days=i), action_completed=f"Day {i}")
            )
        streak = await tracker.get_streak()
        assert streak == 3

    async def test_streak_breaks_on_gap(self) -> None:
        today = date.today()
        await tracker.log_progress(
            ProgressEntry(entry_date=today, action_completed="Today")
        )
        # Skip yesterday, log day-before-yesterday
        await tracker.log_progress(
            ProgressEntry(entry_date=today - timedelta(days=2), action_completed="Old")
        )
        streak = await tracker.get_streak()
        assert streak == 1

    async def test_weekly_summary(self) -> None:
        await tracker.log_progress(
            ProgressEntry(entry_date=date.today(), action_completed="Task", mood_score=7, energy_score=6)
        )
        summary = await tracker.get_weekly_summary()
        assert summary["days_logged"] >= 1
        assert summary["actions_completed"] >= 1
        assert summary["avg_mood"] > 0


class TestLifeMapPersistence:
    async def test_save_and_load_life_map(self) -> None:
        profile = UserProfile(
            name="Map User",
            life_scores=[LifeScore(area=LifeArea.CAREER, current_score=7, target_score=9)],
        )
        lm = LifeMap(profile=profile, insights=["Focus on career growth"])
        row_id = await tracker.save_life_map(lm)
        assert row_id > 0

        loaded = await tracker.load_life_map()
        assert loaded is not None
        assert loaded.profile.name == "Map User"
        assert len(loaded.insights) == 1

    async def test_load_empty_returns_none(self) -> None:
        loaded = await tracker.load_life_map()
        assert loaded is None

    async def test_life_score_trend_empty(self) -> None:
        trend = await tracker.get_life_score_trend()
        assert trend == []

    async def test_life_score_trend_with_data(self) -> None:
        profile = UserProfile(
            name="Trend User",
            life_scores=[
                LifeScore(area=LifeArea.HEALTH, current_score=5, target_score=8),
            ],
        )
        lm = LifeMap(profile=profile)
        await tracker.save_life_map(lm)

        trend = await tracker.get_life_score_trend()
        assert len(trend) == 1
        assert "health" in trend[0]["scores"]
