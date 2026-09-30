"""Tests for Compass Pydantic models."""

from datetime import date, datetime

import pytest

from compass.models import (
    DailyAction,
    Goal,
    LifeArea,
    LifeMap,
    LifeScore,
    ProgressEntry,
    UserProfile,
    WeeklyPlan,
)


class TestLifeArea:
    def test_all_areas_exist(self) -> None:
        areas = [e.value for e in LifeArea]
        assert "career" in areas
        assert "finances" in areas
        assert "health" in areas
        assert "relationships" in areas
        assert "personal_growth" in areas
        assert "creativity" in areas

    def test_area_count(self) -> None:
        assert len(LifeArea) == 6


class TestLifeScore:
    def test_valid_score(self) -> None:
        ls = LifeScore(area=LifeArea.CAREER, current_score=7, target_score=9, notes="Going well")
        assert ls.current_score == 7
        assert ls.target_score == 9
        assert ls.notes == "Going well"

    def test_score_boundaries(self) -> None:
        ls_min = LifeScore(area=LifeArea.HEALTH, current_score=1, target_score=1)
        ls_max = LifeScore(area=LifeArea.HEALTH, current_score=10, target_score=10)
        assert ls_min.current_score == 1
        assert ls_max.current_score == 10

    def test_invalid_score_too_low(self) -> None:
        with pytest.raises(ValueError):
            LifeScore(area=LifeArea.HEALTH, current_score=0, target_score=5)

    def test_invalid_score_too_high(self) -> None:
        with pytest.raises(ValueError):
            LifeScore(area=LifeArea.HEALTH, current_score=11, target_score=5)


class TestGoal:
    def test_basic_goal(self) -> None:
        g = Goal(description="Get promoted", area=LifeArea.CAREER, priority=1)
        assert g.description == "Get promoted"
        assert g.progress_pct == 0.0

    def test_goal_with_milestones(self) -> None:
        g = Goal(
            description="Run a marathon",
            area=LifeArea.HEALTH,
            milestones=["5K", "10K", "Half marathon", "Marathon"],
            progress_pct=25.0,
        )
        assert len(g.milestones) == 4
        assert g.progress_pct == 25.0

    def test_goal_priority_bounds(self) -> None:
        with pytest.raises(ValueError):
            Goal(description="Bad", area=LifeArea.CAREER, priority=0)
        with pytest.raises(ValueError):
            Goal(description="Bad", area=LifeArea.CAREER, priority=6)


class TestUserProfile:
    def test_minimal_profile(self) -> None:
        p = UserProfile(name="Alice")
        assert p.name == "Alice"
        assert p.life_scores == []
        assert p.goals == []
        assert isinstance(p.created_at, datetime)

    def test_full_profile(self) -> None:
        p = UserProfile(
            name="Bob",
            age=35,
            location="NYC",
            profession="Engineer",
            life_scores=[
                LifeScore(area=LifeArea.CAREER, current_score=8, target_score=9),
            ],
            goals=[Goal(description="Lead a team", area=LifeArea.CAREER)],
            values=["Growth", "Family"],
            constraints=["Limited time"],
        )
        assert p.age == 35
        assert len(p.life_scores) == 1
        assert len(p.values) == 2

    def test_profile_serialization_roundtrip(self) -> None:
        p = UserProfile(
            name="Carol",
            age=28,
            profession="Designer",
            life_scores=[
                LifeScore(area=LifeArea.CREATIVITY, current_score=9, target_score=10),
            ],
        )
        json_str = p.model_dump_json()
        p2 = UserProfile.model_validate_json(json_str)
        assert p2.name == "Carol"
        assert p2.life_scores[0].current_score == 9


class TestDailyAction:
    def test_basic_action(self) -> None:
        a = DailyAction(
            description="Meditate for 10 minutes",
            area=LifeArea.HEALTH,
            difficulty=2,
            time_minutes=10,
            why_this_matters="Reduces stress before the work day",
        )
        assert a.time_minutes == 10
        assert a.difficulty == 2

    def test_action_defaults(self) -> None:
        a = DailyAction(description="Read", area=LifeArea.PERSONAL_GROWTH)
        assert a.difficulty == 2
        assert a.time_minutes == 15
        assert a.linked_goal is None


class TestWeeklyPlan:
    def test_basic_plan(self) -> None:
        wp = WeeklyPlan(
            week_number=1,
            actions=[
                DailyAction(description="Walk", area=LifeArea.HEALTH),
            ],
            focus_area=LifeArea.HEALTH,
            reflection_prompt="How did movement affect your energy?",
            affirmation="I am becoming healthier every day.",
        )
        assert wp.week_number == 1
        assert len(wp.actions) == 1
        assert wp.focus_area == LifeArea.HEALTH


class TestProgressEntry:
    def test_defaults(self) -> None:
        pe = ProgressEntry()
        assert pe.entry_date == date.today()
        assert pe.mood_score == 5
        assert pe.energy_score == 5

    def test_mood_bounds(self) -> None:
        with pytest.raises(ValueError):
            ProgressEntry(mood_score=0)
        with pytest.raises(ValueError):
            ProgressEntry(mood_score=11)


class TestLifeMap:
    def test_life_map_construction(self) -> None:
        profile = UserProfile(name="Dan")
        lm = LifeMap(
            profile=profile,
            goals=[Goal(description="Learn piano", area=LifeArea.CREATIVITY)],
            insights=["Focus on creativity for maximum fulfillment"],
            next_milestone="Complete first song",
        )
        assert lm.profile.name == "Dan"
        assert len(lm.goals) == 1
        assert lm.next_milestone == "Complete first song"

    def test_life_map_serialization(self) -> None:
        profile = UserProfile(name="Eve")
        lm = LifeMap(profile=profile)
        json_str = lm.model_dump_json()
        lm2 = LifeMap.model_validate_json(json_str)
        assert lm2.profile.name == "Eve"
