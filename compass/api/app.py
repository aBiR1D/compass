"""FastAPI application — REST API for the Compass life strategist."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from compass.models import DailyAction, LifeMap, ProgressEntry, WeeklyPlan
from compass.strategist import (
    generate_daily_actions,
    generate_life_map,
    generate_weekly_plan,
    weekly_checkin,
)
from compass.tracker import (
    get_progress,
    load_life_map,
    load_profile,
    log_progress,
    save_life_map,
    save_profile,
)

app = FastAPI(
    title="Compass API",
    description="AI Life Strategist — personalized micro-actions that compound into massive change",
    version="0.1.0",
)


class InterviewMessage(BaseModel):
    message: str


class InterviewResponse(BaseModel):
    reply: str
    profile_ready: bool = False


class ProgressRequest(BaseModel):
    action_completed: str = ""
    notes: str = ""
    mood_score: int = 5
    energy_score: int = 5


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse()


@app.post("/api/v1/interview", response_model=InterviewResponse)
async def interview(body: InterviewMessage) -> InterviewResponse:
    """Start or continue the life interview.

    This is a simplified single-turn endpoint — for a full multi-turn interview
    use the CLI (``compass start``).
    """
    from compass.ai import chat
    from compass.interviewer import INTERVIEW_SYSTEM, _extract_profile

    reply = await chat(
        system=INTERVIEW_SYSTEM,
        messages=[{"role": "user", "content": body.message}],
    )
    ready = '"profile_ready"' in reply and "true" in reply.lower()
    if ready:
        profile = _extract_profile(reply, [])
        await save_profile(profile)
    return InterviewResponse(reply=reply, profile_ready=ready)


@app.get("/api/v1/today", response_model=list[DailyAction])
async def get_today() -> list[DailyAction]:
    """Get today's personalized actions."""
    profile = await load_profile()
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile found. Complete the interview first.")
    return await generate_daily_actions(profile)


@app.get("/api/v1/week", response_model=WeeklyPlan)
async def get_week() -> WeeklyPlan:
    """Get this week's plan."""
    profile = await load_profile()
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile found. Complete the interview first.")
    week_num = date.today().isocalendar()[1]
    return await generate_weekly_plan(profile, week_num)


@app.post("/api/v1/progress")
async def post_progress(body: ProgressRequest) -> dict:
    """Log daily progress."""
    entry = ProgressEntry(
        entry_date=date.today(),
        action_completed=body.action_completed,
        notes=body.notes,
        mood_score=max(1, min(10, body.mood_score)),
        energy_score=max(1, min(10, body.energy_score)),
    )
    row_id = await log_progress(entry)
    return {"id": row_id, "status": "logged"}


@app.get("/api/v1/map", response_model=LifeMap)
async def get_map() -> LifeMap:
    """Get the full life map."""
    life_map = await load_life_map()
    if life_map is not None:
        return life_map
    profile = await load_profile()
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile found. Complete the interview first.")
    life_map = await generate_life_map(profile)
    await save_life_map(life_map)
    return life_map
