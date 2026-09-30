"""MCP server for the Compass life strategist."""

from __future__ import annotations

import asyncio
import json
from datetime import date, timedelta

from mcp.server.fastmcp import FastMCP

from compass.models import ProgressEntry

mcp = FastMCP(
    "compass",
    description="AI Life Strategist — personalized daily micro-actions",
)


@mcp.tool()
async def get_daily_actions() -> str:
    """Get today's personalized micro-actions based on your life profile."""
    from compass.strategist import generate_daily_actions
    from compass.tracker import load_profile

    profile = await load_profile()
    if profile is None:
        return json.dumps({"error": "No profile found. Run `compass start` first."})
    actions = await generate_daily_actions(profile)
    return json.dumps([a.model_dump(mode="json") for a in actions], indent=2)


@mcp.tool()
async def get_life_map() -> str:
    """Get your current life strategy map with goals, scores, and insights."""
    from compass.strategist import generate_life_map
    from compass.tracker import load_life_map, load_profile, save_life_map

    life_map = await load_life_map()
    if life_map is None:
        profile = await load_profile()
        if profile is None:
            return json.dumps({"error": "No profile found. Run `compass start` first."})
        life_map = await generate_life_map(profile)
        await save_life_map(life_map)
    return life_map.model_dump_json(indent=2)


@mcp.tool()
async def weekly_checkin_tool() -> str:
    """Run a weekly AI check-in — review progress and get updated strategy."""
    from compass.strategist import weekly_checkin
    from compass.tracker import get_progress, load_profile

    profile = await load_profile()
    if profile is None:
        return json.dumps({"error": "No profile found. Run `compass start` first."})
    week_start = date.today() - timedelta(days=date.today().weekday())
    progress = await get_progress(since=week_start)
    result = await weekly_checkin(profile, progress)
    return json.dumps(result, indent=2)


@mcp.tool()
async def log_progress_tool(
    action_completed: str,
    notes: str = "",
    mood_score: int = 5,
    energy_score: int = 5,
) -> str:
    """Log your daily progress — what you did, mood, and energy level."""
    from compass.tracker import log_progress

    entry = ProgressEntry(
        entry_date=date.today(),
        action_completed=action_completed,
        notes=notes,
        mood_score=max(1, min(10, mood_score)),
        energy_score=max(1, min(10, energy_score)),
    )
    row_id = await log_progress(entry)
    return json.dumps({"id": row_id, "status": "logged"})


def main() -> None:
    """Run the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
