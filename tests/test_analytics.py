from types import SimpleNamespace

from app.services.analytics import PerformanceAnalyzer


def make_stat(**overrides):
    defaults = dict(
        matches=1, distance=8, minutes=90, challenges=3,
        goals=1, assists=1, injuries=0,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_empty_history_returns_beginner_defaults():
    result = PerformanceAnalyzer([]).analyze()
    assert result["level"] == "Beginner"
    assert result["score"] == 0
    assert result["reviews"] == []


def test_declining_distance_is_flagged():
    stats = [make_stat(distance=d) for d in [10, 8, 6, 3]]
    result = PerformanceAnalyzer(stats).analyze()
    assert any("trending down" in review for review in result["reviews"])


def test_no_goals_prompts_finishing_advice():
    stats = [make_stat(goals=0)]
    result = PerformanceAnalyzer(stats).analyze()
    assert any("Time to score" in review for review in result["reviews"])


def test_injury_is_flagged():
    stats = [make_stat(injuries=1)]
    result = PerformanceAnalyzer(stats).analyze()
    assert any("injury" in review for review in result["reviews"])


def test_injury_reduces_score():
    healthy = PerformanceAnalyzer([make_stat(injuries=0)]).analyze()["score"]
    injured = PerformanceAnalyzer([make_stat(injuries=1)]).analyze()["score"]
    assert injured < healthy


def test_score_never_goes_below_zero():
    stats = [make_stat(matches=0, distance=0, goals=0, assists=0, challenges=0, injuries=10)]
    result = PerformanceAnalyzer(stats).analyze()
    assert result["score"] == 0


def test_rising_challenges_is_flagged():
    stats = [make_stat(challenges=c) for c in [1, 2, 4, 8]]
    result = PerformanceAnalyzer(stats).analyze()
    assert any("Challenges won is trending up" in review for review in result["reviews"])


def test_advice_is_deterministic_not_random():
    stats = [make_stat(goals=0)]
    first = PerformanceAnalyzer(stats).analyze()["advice"]
    second = PerformanceAnalyzer(stats).analyze()["advice"]
    assert first == second
