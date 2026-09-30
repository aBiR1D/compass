"""Pydantic models for the Compass life strategist."""

from datetime import UTC, date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LifeArea(str, Enum):
    """Core life domains tracked by Compass."""

    CAREER = "career"
    FINANCES = "finances"
    HEALTH = "health"
    RELATIONSHIPS = "relationships"
    PERSONAL_GROWTH = "personal_growth"
    CREATIVITY = "creativity"


class LifeScore(BaseModel):
    """Current and target score for a single life area."""

    area: LifeArea
    current_score: int = Field(ge=1, le=10, description="Where you are now (1-10)")
    target_score: int = Field(ge=1, le=10, description="Where you want to be (1-10)")
    notes: str = ""


class Goal(BaseModel):
    """A specific, actionable life goal."""

    description: str
    area: LifeArea
    target_date: Optional[date] = None
    priority: int = Field(default=3, ge=1, le=5, description="1=highest, 5=lowest")
    milestones: list[str] = Field(default_factory=list)
    progress_pct: float = Field(default=0.0, ge=0.0, le=100.0)


class UserProfile(BaseModel):
    """Complete snapshot of who the user is."""

    name: str
    age: Optional[int] = None
    location: str = ""
    profession: str = ""
    life_scores: list[LifeScore] = Field(default_factory=list)
    goals: list[Goal] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DailyAction(BaseModel):
    """One concrete micro-action for today."""

    description: str
    area: LifeArea
    difficulty: int = Field(default=2, ge=1, le=5, description="1=trivial, 5=hard")
    time_minutes: int = Field(default=15, ge=1)
    why_this_matters: str = ""
    linked_goal: Optional[str] = None


class WeeklyPlan(BaseModel):
    """A week's worth of strategy and actions."""

    week_number: int = Field(ge=1)
    actions: list[DailyAction] = Field(default_factory=list)
    focus_area: LifeArea = LifeArea.PERSONAL_GROWTH
    reflection_prompt: str = ""
    affirmation: str = ""


class ProgressEntry(BaseModel):
    """Daily progress log entry."""

    entry_date: date = Field(default_factory=date.today)
    action_completed: str = ""
    notes: str = ""
    mood_score: int = Field(default=5, ge=1, le=10)
    energy_score: int = Field(default=5, ge=1, le=10)


class LifeMap(BaseModel):
    """The complete, living document of your life strategy."""

    profile: UserProfile
    goals: list[Goal] = Field(default_factory=list)
    current_week_plan: Optional[WeeklyPlan] = None
    progress_history: list[ProgressEntry] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    next_milestone: str = ""
