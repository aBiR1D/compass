"""AI-powered life interview — builds a complete UserProfile interactively."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from compass.ai import chat, parse_json_response
from compass.models import Goal, LifeArea, LifeScore, UserProfile

console = Console()

INTERVIEW_SYSTEM = """\
You are Compass, an expert life strategist with the warmth of a therapist, the \
analytical mind of a McKinsey consultant, and the motivational energy of a world-class \
coach. You are conducting an initial life interview.

RULES:
- Ask ONE question at a time.
- Be empathetic, curious, and non-judgmental.
- Use the user's previous answers to ask follow-up questions.
- After gathering enough information for a section, move on.
- When you have enough data, output ONLY a JSON object (no markdown fences) with the \
key "profile_ready": true plus a "profile" object matching the UserProfile schema.

The interview covers:
1. Basics (name, age, location, profession)
2. Life satisfaction scores across 6 areas (career, finances, health, \
relationships, personal_growth, creativity) — current and target, 1-10
3. Top goals and aspirations
4. Core values (what matters most)
5. Constraints (time, money, family obligations, etc.)

Keep it conversational, not like a form.\
"""


async def _run_interview_loop() -> UserProfile:
    """Drive the multi-turn interview conversation."""
    history: list[dict[str, str]] = []

    console.print(
        Panel(
            "[bold cyan]Welcome to Compass[/]\n\n"
            "I'm going to ask you a series of questions to build your personal life map.\n"
            "Take your time — there are no wrong answers.\n"
            "Type [bold yellow]quit[/] at any prompt to stop early.",
            title="🧭 Life Interview",
            border_style="cyan",
        )
    )

    # Kick off the conversation
    opening = await chat(
        system=INTERVIEW_SYSTEM,
        messages=[{"role": "user", "content": "Let's begin the interview."}],
    )
    history.append({"role": "user", "content": "Let's begin the interview."})
    history.append({"role": "assistant", "content": opening})
    console.print(f"\n[bold green]Compass:[/] {opening}\n")

    while True:
        answer = Prompt.ask("[bold yellow]You")
        if answer.lower() in {"quit", "exit", "q"}:
            console.print("[dim]Wrapping up early — building profile from what we have…[/]")
            history.append(
                {"role": "user", "content": "Please wrap up and generate the profile JSON now."}
            )
            reply = await chat(system=INTERVIEW_SYSTEM, messages=history)
            history.append({"role": "assistant", "content": reply})
            break

        history.append({"role": "user", "content": answer})
        reply = await chat(system=INTERVIEW_SYSTEM, messages=history)
        history.append({"role": "assistant", "content": reply})

        # Check if the model decided it has enough
        if '"profile_ready"' in reply and "true" in reply.lower():
            break

        console.print(f"\n[bold green]Compass:[/] {reply}\n")

    # Extract profile
    return _extract_profile(reply, history)


def _extract_profile(final_reply: str, history: list[dict[str, str]]) -> UserProfile:
    """Parse the model's final JSON into a UserProfile."""
    try:
        data = parse_json_response(final_reply)
        profile_data = data.get("profile", data)
    except (json.JSONDecodeError, KeyError):
        # Fallback: build a minimal profile from history
        profile_data = {"name": "User", "life_scores": [], "goals": [], "values": []}

    life_scores = []
    for ls in profile_data.get("life_scores", []):
        try:
            life_scores.append(LifeScore(**ls))
        except Exception:
            continue

    goals = []
    for g in profile_data.get("goals", []):
        try:
            goals.append(Goal(**g))
        except Exception:
            continue

    return UserProfile(
        name=profile_data.get("name", "User"),
        age=profile_data.get("age"),
        location=profile_data.get("location", ""),
        profession=profile_data.get("profession", ""),
        life_scores=life_scores,
        goals=goals,
        values=profile_data.get("values", []),
        constraints=profile_data.get("constraints", []),
        created_at=datetime.now(UTC),
    )


def conduct_interview() -> UserProfile:
    """Run the full interactive interview (blocking entry-point for the CLI)."""
    return asyncio.run(_run_interview_loop())


async def assess_life_areas(context: str) -> list[LifeScore]:
    """Given free-text context, return scored life areas."""
    system = (
        "You are a life assessment expert. Given a description of someone's life, "
        "rate each of these 6 areas on a 1-10 scale (current and target): "
        "career, finances, health, relationships, personal_growth, creativity. "
        "Return ONLY a JSON array of objects with keys: area, current_score, target_score, notes."
    )
    raw = await chat(system=system, messages=[{"role": "user", "content": context}])
    items = parse_json_response(raw) if raw.strip().startswith("[") else parse_json_response(f"[{raw}]")
    if isinstance(items, dict):
        items = items.get("scores", [items])
    return [LifeScore(**item) for item in items]


async def extract_goals(context: str) -> list[Goal]:
    """Given free-text context, extract and prioritize goals."""
    system = (
        "You are a goal-setting expert. From the user's description, extract concrete goals. "
        "Return ONLY a JSON array of objects with keys: description, area (one of career, "
        "finances, health, relationships, personal_growth, creativity), priority (1-5), milestones (list of strings)."
    )
    raw = await chat(system=system, messages=[{"role": "user", "content": context}])
    items = parse_json_response(raw) if raw.strip().startswith("[") else []
    return [Goal(**item) for item in items]


async def deep_dive(area: LifeArea, profile: UserProfile) -> str:
    """Conduct a deep-dive analysis of one life area."""
    system = (
        f"You are an expert life strategist. The user wants a deep dive into their "
        f"{area.value} situation. Analyze their profile and provide: "
        f"1) Current state assessment, 2) Key leverage points, 3) Quick wins, "
        f"4) Long-term strategy. Be specific, not generic."
    )
    return await chat(
        system=system,
        messages=[{"role": "user", "content": profile.model_dump_json(indent=2)}],
    )
