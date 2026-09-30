"""Compass CLI — Beautiful terminal interface powered by Typer + Rich."""

from __future__ import annotations

import asyncio
from datetime import date

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from compass.models import LifeArea, ProgressEntry

app = typer.Typer(
    name="compass",
    help="🧭 Compass — Your AI Life Strategist",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()

BANNER = r"""
   ██████╗ ██████╗ ███╗   ███╗██████╗  █████╗ ███████╗███████╗
  ██╔════╝██╔═══██╗████╗ ████║██╔══██╗██╔══██╗██╔════╝██╔════╝
  ██║     ██║   ██║██╔████╔██║██████╔╝███████║███████╗███████╗
  ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══██║╚════██║╚════██║
  ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ██║  ██║███████║███████║
   ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝
"""

_AREA_COLORS = {
    LifeArea.CAREER: "blue",
    LifeArea.FINANCES: "green",
    LifeArea.HEALTH: "red",
    LifeArea.RELATIONSHIPS: "magenta",
    LifeArea.PERSONAL_GROWTH: "yellow",
    LifeArea.CREATIVITY: "cyan",
}


def _score_bar(score: int, width: int = 20) -> Text:
    filled = int(score / 10 * width)
    color = "red" if score <= 3 else ("yellow" if score <= 6 else "green")
    bar = Text("█" * filled, style=color)
    bar.append("░" * (width - filled), style="dim")
    bar.append(f" {score}/10")
    return bar


def _print_banner() -> None:
    console.print(Text(BANNER, style="bold cyan"))
    console.print("[dim]Your AI Life Strategist[/]\n")


# ── Commands ──────────────────────────────────────────────────────────


@app.command()
def start() -> None:
    """Begin the life interview — build your personal profile."""
    from compass.interviewer import conduct_interview
    from compass.tracker import save_profile

    _print_banner()
    profile = conduct_interview()
    asyncio.run(save_profile(profile))
    console.print(
        Panel(
            f"[bold green]Profile created for {profile.name}![/]\n"
            f"Run [bold cyan]compass map[/] to generate your life map.",
            title="✅ Interview Complete",
            border_style="green",
        )
    )


@app.command()
def today() -> None:
    """Show today's personalized actions."""
    from compass.strategist import generate_daily_actions
    from compass.tracker import load_profile

    _print_banner()
    profile = asyncio.run(load_profile())
    if profile is None:
        console.print("[red]No profile found. Run `compass start` first.[/]")
        raise typer.Exit(1)

    actions = asyncio.run(generate_daily_actions(profile))
    table = Table(title=f"📋 Today's Actions — {date.today().strftime('%A, %B %d')}", show_lines=True)
    table.add_column("", width=3)
    table.add_column("Action", min_width=30)
    table.add_column("Area", width=16)
    table.add_column("Time", width=8, justify="right")
    table.add_column("Why", min_width=20)

    for i, action in enumerate(actions, 1):
        color = _AREA_COLORS.get(action.area, "white")
        table.add_row(
            f"☐ {i}",
            action.description,
            f"[{color}]{action.area.value}[/]",
            f"{action.time_minutes}m",
            f"[dim]{action.why_this_matters}[/]",
        )
    console.print(table)


@app.command()
def week() -> None:
    """Show this week's plan."""
    from compass.strategist import generate_weekly_plan
    from compass.tracker import load_profile

    _print_banner()
    profile = asyncio.run(load_profile())
    if profile is None:
        console.print("[red]No profile found. Run `compass start` first.[/]")
        raise typer.Exit(1)

    import datetime as _dt
    week_num = date.today().isocalendar()[1]
    plan = asyncio.run(generate_weekly_plan(profile, week_num))

    console.print(
        Panel(
            f"[bold]Focus Area:[/] [{_AREA_COLORS.get(plan.focus_area, 'white')}]"
            f"{plan.focus_area.value}[/]\n\n"
            f"[bold]Affirmation:[/] [italic]{plan.affirmation}[/]",
            title=f"📅 Week {plan.week_number} Plan",
            border_style="cyan",
        )
    )

    table = Table(show_lines=True)
    table.add_column("#", width=3)
    table.add_column("Action", min_width=30)
    table.add_column("Area", width=16)
    table.add_column("Difficulty", width=10)
    table.add_column("Time", width=8, justify="right")

    for i, action in enumerate(plan.actions, 1):
        color = _AREA_COLORS.get(action.area, "white")
        diff_stars = "⭐" * action.difficulty
        table.add_row(
            str(i),
            action.description,
            f"[{color}]{action.area.value}[/]",
            diff_stars,
            f"{action.time_minutes}m",
        )
    console.print(table)

    if plan.reflection_prompt:
        console.print(
            Panel(
                f"[italic]{plan.reflection_prompt}[/]",
                title="🤔 Weekly Reflection",
                border_style="yellow",
            )
        )


@app.command()
def log() -> None:
    """Log today's progress (interactive)."""
    from rich.prompt import IntPrompt, Prompt

    from compass.tracker import log_progress

    _print_banner()
    console.print("[bold]📝 Daily Progress Log[/]\n")

    action = Prompt.ask("What did you accomplish today?")
    notes = Prompt.ask("Any notes or reflections?", default="")
    mood = IntPrompt.ask("Mood score (1-10)", default=5)
    energy = IntPrompt.ask("Energy score (1-10)", default=5)

    entry = ProgressEntry(
        entry_date=date.today(),
        action_completed=action,
        notes=notes,
        mood_score=max(1, min(10, mood)),
        energy_score=max(1, min(10, energy)),
    )
    asyncio.run(log_progress(entry))
    console.print("\n[bold green]✅ Progress logged![/]")

    streak = asyncio.run(__import__("compass.tracker", fromlist=["get_streak"]).get_streak())
    if streak > 0:
        console.print(f"[bold yellow]🔥 Current streak: {streak} day{'s' if streak != 1 else ''}[/]")


@app.command()
def checkin() -> None:
    """Run a weekly AI check-in."""
    from compass.strategist import weekly_checkin
    from compass.tracker import get_progress, load_profile

    _print_banner()
    profile = asyncio.run(load_profile())
    if profile is None:
        console.print("[red]No profile found. Run `compass start` first.[/]")
        raise typer.Exit(1)

    from datetime import timedelta

    week_start = date.today() - timedelta(days=date.today().weekday())
    progress = asyncio.run(get_progress(since=week_start))
    result = asyncio.run(weekly_checkin(profile, progress))

    console.print(
        Panel(
            f"[bold]{result.get('summary', '')}[/]",
            title="📊 Weekly Check-in",
            border_style="cyan",
        )
    )
    if result.get("insights"):
        console.print("\n[bold]💡 Insights:[/]")
        for insight in result["insights"]:
            console.print(f"  • {insight}")

    if result.get("adjustments"):
        console.print("\n[bold]🔄 Adjustments:[/]")
        for adj in result["adjustments"]:
            console.print(f"  • {adj}")

    if result.get("encouragement"):
        console.print(
            Panel(
                f"[italic green]{result['encouragement']}[/]",
                border_style="green",
            )
        )


@app.command(name="map")
def show_map() -> None:
    """Display your life map."""
    from compass.strategist import generate_life_map
    from compass.tracker import load_life_map, load_profile, save_life_map

    _print_banner()
    life_map = asyncio.run(load_life_map())
    if life_map is None:
        profile = asyncio.run(load_profile())
        if profile is None:
            console.print("[red]No profile found. Run `compass start` first.[/]")
            raise typer.Exit(1)
        console.print("[dim]Generating your life map…[/]")
        life_map = asyncio.run(generate_life_map(profile))
        asyncio.run(save_life_map(life_map))

    console.print(
        Panel(
            f"[bold]{life_map.profile.name}'s Life Map[/]",
            title="🗺️  Life Map",
            border_style="cyan",
        )
    )

    # Goals
    if life_map.goals:
        table = Table(title="🎯 Goals", show_lines=True)
        table.add_column("Goal", min_width=30)
        table.add_column("Area", width=16)
        table.add_column("Priority", width=8)
        table.add_column("Progress", width=15)
        for g in life_map.goals:
            color = _AREA_COLORS.get(g.area, "white")
            pbar = _score_bar(int(g.progress_pct / 10), width=10)
            table.add_row(
                g.description,
                f"[{color}]{g.area.value}[/]",
                "⭐" * g.priority,
                pbar,
            )
        console.print(table)

    # Insights
    if life_map.insights:
        console.print("\n[bold]💡 Strategic Insights:[/]")
        for insight in life_map.insights:
            console.print(f"  • {insight}")

    # Next milestone
    if life_map.next_milestone:
        console.print(
            Panel(
                f"[bold yellow]{life_map.next_milestone}[/]",
                title="🏁 Next Milestone",
                border_style="yellow",
            )
        )


@app.command()
def score() -> None:
    """Show your life area scores."""
    from compass.tracker import load_profile

    _print_banner()
    profile = asyncio.run(load_profile())
    if profile is None:
        console.print("[red]No profile found. Run `compass start` first.[/]")
        raise typer.Exit(1)

    if not profile.life_scores:
        console.print("[yellow]No life scores recorded yet.[/]")
        raise typer.Exit(0)

    console.print(Panel("[bold]Life Area Scores[/]", title="📊 Score Board", border_style="cyan"))
    for ls in profile.life_scores:
        color = _AREA_COLORS.get(ls.area, "white")
        label = f"[{color}]{ls.area.value:<18}[/]"
        current_bar = _score_bar(ls.current_score)
        target = f"  → target: {ls.target_score}/10"
        console.print(f"  {label} {current_bar}{target}")
        if ls.notes:
            console.print(f"  {'':18}  [dim]{ls.notes}[/]")
    console.print()


def _cli_entry() -> None:
    """Entry point for ``python -m compass``."""
    app()
