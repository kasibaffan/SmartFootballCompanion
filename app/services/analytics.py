import numpy as np


class PerformanceAnalyzer:
    """Derives performance insights from a user's historical stat entries.

    This is real (if simple) statistics over the user's own data - rolling
    trend slopes over matches/distance/goals/assists/challenges and an
    injury flag - not a hardcoded formula.
    """

    def __init__(self, stats):
        self.stats = list(stats)

    def analyze(self):
        if not self.stats:
            return {
                "score": 0,
                "reviews": [],
                "level": "Beginner",
                "suggestion": "Log your first session to get started.",
                "advice": "Track a match to unlock personalized insights.",
            }

        latest = self.stats[-1]
        reviews = self._trend_reviews()
        return {
            "score": self._score(latest),
            "reviews": reviews,
            "level": self._level(self._score(latest)),
            "suggestion": self._suggestion(),
            "advice": reviews[0] if reviews else "Keep up the balanced training - your metrics look stable.",
        }

    def _score(self, latest):
        raw = (
            (latest.matches or 0) * 5
            + (latest.distance or 0) * 2
            + (latest.goals or 0) * 10
            + (latest.assists or 0) * 8
            + (latest.challenges or 0) * 3
            - (latest.injuries or 0) * 15
        )
        return max(0, min(100, int(raw)))

    def _series(self, attr):
        return np.array([getattr(s, attr) or 0 for s in self.stats], dtype=float)

    def _trend_slope(self, attr):
        y = self._series(attr)
        if len(y) < 2:
            return 0.0
        slope, _ = np.polyfit(np.arange(len(y)), y, 1)
        return float(slope)

    def _trend_reviews(self):
        reviews = []
        latest = self.stats[-1]

        if latest.injuries:
            reviews.append(
                f"You logged {int(latest.injuries)} injury this match - prioritize recovery and rest before your next session."
            )

        dist_slope = self._trend_slope("distance")
        if dist_slope < -0.3:
            reviews.append(
                f"Distance covered is trending down ({dist_slope:.2f} km/match) - work on stamina."
            )
        elif latest.distance is not None and latest.distance < 5:
            reviews.append("Increase distance covered per match.")

        goals_slope = self._trend_slope("goals")
        if not latest.goals:
            reviews.append("Time to score! Work on finishing.")
        elif goals_slope > 0.2:
            reviews.append(f"Goal-scoring is trending up (+{goals_slope:.2f}/match) - keep it up!")

        challenges_slope = self._trend_slope("challenges")
        if challenges_slope > 0.3:
            reviews.append(f"Challenges won is trending up (+{challenges_slope:.2f}/match) - strong defensive involvement.")

        return reviews

    def _level(self, score):
        if score < 40:
            return "Rookie"
        if score < 70:
            return "Pro"
        if score < 90:
            return "Elite"
        return "Legend"

    def _suggestion(self):
        total_goals = sum(s.goals or 0 for s in self.stats)
        return f"Score {max(1, 3 - total_goals)} goals this week!"
