"""Strategy engine — generates personalized life maps, weekly plans, and daily actions."""

from __future__ import annotations

import json
from datetime import date, timedelta

from compass.ai import chat, parse_json_response
from compass.models import (
    DailyAction,
    Goal,
    LifeArea,
    LifeMap,
    ProgressEntry,
    UserProfile,
    WeeklyPlan,
)

STRATEGIST_SYSTEM = """\
You are Compass, an elite life strategist. You create hyper-personalized action plans \
based on detailed knowledge of the user's life. Every recommendation must be:
1. SPECIFIC to this person's situation (reference their goals, constraints, profession)
2. ACTIONABLE within their time/energy constraints
3. COMPOUNDING — small actions that build on each other
4. MEASURABLE — the user can clearly tell if they did it

Never give generic advice like "exercise more" or "read a book". Instead: \
"Do a 7-minute HIIT workout before your 9am standup" or "Read 10 pages of \
'Thinking, Fast and Slow' during your lunch break".\
"""


async def generate_life_map(profile: UserProfile) -> LifeMap:
    """Create a comprehensive life strategy map from a user profile."""
    prompt = (
        "Generate a complete life strategy map for this person. Return JSON with keys:\n"
        '- "goals": array of goals with description, area, priority (1-5), milestones\n'
        '- "current_week_plan": object with week_number, actions (each with description, '
        "area, difficulty 1-5, time_minutes, why_this_matters, linked_goal), "
        "focus_area, reflection_prompt, affirmation\n"
        '- "insights": array of 3-5 strategic insights\n'
        '- "next_milestone": string describing the next big milestone\n\n'
        f"Profile:\n{profile.model_dump_json(indent=2)}"
    )
    raw = await chat(system=STRATEGIST_SYSTEM, messages=[{"role": "user", "content": prompt}])
    data = parse_json_response(raw)

    goals = [Goal(**g) for g in data.get("goals", [])]
    wp_data = data.get("current_week_plan", {})
    actions = [DailyAction(**a) for a in wp_data.get("actions", [])]
    week_plan = WeeklyPlan(
        week_number=wp_data.get("week_number", 1),
        actions=actions,
        focus_area=wp_data.get("focus_area", LifeArea.PERSONAL_GROWTH),
        reflection_prompt=wp_data.get("reflection_prompt", ""),
        affirmation=wp_data.get("affirmation", ""),
    )

    return LifeMap(
        profile=profile,
        goals=goals,
        current_week_plan=week_plan,
        progress_history=[],
        insights=data.get("insights", []),
        next_milestone=data.get("next_milestone", ""),
    )


async def generate_weekly_plan(profile: UserProfile, week: int) -> WeeklyPlan:
    """Generate a focused plan for a specific week."""
    prompt = (
        f"Generate a detailed weekly plan for week {week}. The plan should have "
        f"5-7 daily actions spread across the week, a focus area, a reflection prompt, "
        f"and an affirmation. Return JSON matching this schema:\n"
        f'{{"week_number": {week}, "actions": [...], "focus_area": "...", '
        f'"reflection_prompt": "...", "affirmation": "..."}}\n\n'
        f"Profile:\n{profile.model_dump_json(indent=2)}"
    )
    raw = await chat(system=STRATEGIST_SYSTEM, messages=[{"role": "user", "content": prompt}])
    data = parse_json_response(raw)
    actions = [DailyAction(**a) for a in data.get("actions", [])]
    return WeeklyPlan(
        week_number=data.get("week_number", week),
        actions=actions,
        focus_area=data.get("focus_area", LifeArea.PERSONAL_GROWTH),
        reflection_prompt=data.get("reflection_prompt", ""),
        affirmation=data.get("affirmation", ""),
    )


async def generate_daily_actions(profile: UserProfile, day: date | None = None) -> list[DailyAction]:
    """Generate 3-5 personalized actions for a specific day."""
    day = day or date.today()
    weekday = day.strftime("%A")
    prompt = (
        f"Generate 3-5 specific daily actions for {weekday}, {day.isoformat()}. "
        f"Each action needs: description, area, difficulty (1-5), time_minutes, "
        f"why_this_matters, linked_goal. Return a JSON array.\n\n"
        f"Profile:\n{profile.model_dump_json(indent=2)}"
    )
    raw = await chat(system=STRATEGIST_SYSTEM, messages=[{"role": "user", "content": prompt}])
    items = parse_json_response(raw)
    if isinstance(items, dict):
        items = items.get("actions", [])
    return [DailyAction(**item) for item in items]


async def weekly_checkin(
    profile: UserProfile, progress: list[ProgressEntry]
) -> dict:
    """Run a weekly check-in: analyse progress, adjust strategy, provide insights.

    Returns a dict with keys: ``summary``, ``insights``, ``adjustments``, ``encouragement``.
    """
    progress_json = json.dumps([p.model_dump(mode="json") for p in progress], indent=2)
    prompt = (
        "Perform a weekly check-in. Review the user's progress and return JSON with:\n"
        '- "summary": 2-3 sentence recap\n'
        '- "insights": array of strategic observations\n'
        '- "adjustments": array of recommended changes\n'
        '- "encouragement": a motivational closing message\n\n'
        f"Profile:\n{profile.model_dump_json(indent=2)}\n\n"
        f"This week's progress entries:\n{progress_json}"
    )
    raw = await chat(system=STRATEGIST_SYSTEM, messages=[{"role": "user", "content": prompt}])
    return parse_json_response(raw)


async def adapt_plan(profile: UserProfile, feedback: str) -> dict:
    """Adapt the life plan based on user feedback or changed circumstances.

    Returns a dict with ``updated_goals`` and ``reasoning``.
    """
    prompt = (
        "The user's situation has changed. Adapt their plan accordingly. "
        "Return JSON with:\n"
        '- "updated_goals": array of adjusted goals\n'
        '- "reasoning": explanation of what changed and why\n\n'
        f"Profile:\n{profile.model_dump_json(indent=2)}\n\n"
        f"User feedback:\n{feedback}"
    )
    raw = await chat(system=STRATEGIST_SYSTEM, messages=[{"role": "user", "content": prompt}])
    return parse_json_response(raw)
