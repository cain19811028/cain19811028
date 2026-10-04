import unittest
from datetime import datetime, timezone

from helpers import page, repo
from readmegen import github


class SummarizeTest(unittest.TestCase):
    def test_folds_every_page(self):
        first = page(
            repos=[
                repo("a", stars=4, langs=[("Go", 300, "#00ADD8")]),
                repo("b", langs=[("Python", 600, "#3572A5"), ("Go", 100, "#00ADD8")]),
            ],
            total_repos=3,
            counts=[1, 0, 3],
        )
        second = page(repos=[repo("c", stars=7)])
        stats = github.summarize([first, second])
        self.assertEqual((stats.repos, stats.stars, stats.contributions), (3, 11, 4))
        self.assertEqual((stats.commits, stats.pull_requests, stats.issues), (7, 2, 1))
        self.assertEqual(
            [(lang.name, lang.share, lang.color) for lang in stats.languages],
            [("Python", 0.6, "#3572A5"), ("Go", 0.4, "#00ADD8")],
        )
        self.assertEqual([d.level for d in stats.days], [1, 0, 3])
        self.assertEqual([r.name for r in stats.recent], ["a", "b", "c"])
        self.assertIsNone(stats.name)

    def test_featured_prefers_pinned_then_most_starred(self):
        repos = [repo("low", stars=1), repo("high", stars=9), repo("mid", stars=5)]
        pinned = github.summarize([page(repos=repos, pinned=[repo("mine")])])
        self.assertEqual([r.name for r in pinned.featured()], ["mine"])
        unpinned = github.summarize([page(repos=repos)])
        self.assertEqual([r.name for r in unpinned.featured(2)], ["high", "mid"])


class StreakTest(unittest.TestCase):
    def streaks(self, counts):
        return github.summarize([page(counts=counts)]).streaks()

    def test_current_streak_ends_today(self):
        self.assertEqual(self.streaks([1, 0, 2, 2, 2]), (3, 3))

    def test_a_quiet_today_does_not_break_the_streak_yet(self):
        self.assertEqual(self.streaks([1, 1, 0, 4, 4, 0]), (2, 2))

    def test_a_quiet_yesterday_does(self):
        self.assertEqual(self.streaks([5, 5, 5, 5, 0, 0]), (0, 4))

    def test_active_days(self):
        self.assertEqual(github.summarize([page(counts=[1, 0, 2, 0])]).active_days, 2)


class UptimeTest(unittest.TestCase):
    def test_counts_whole_months(self):
        now = datetime(2026, 10, 4, tzinfo=timezone.utc)
        since = datetime(2012, 3, 7, 13, 17, tzinfo=timezone.utc)
        self.assertEqual(github.uptime(since, now), (14, 6))
        self.assertEqual(github.uptime(datetime(2026, 9, 5, tzinfo=timezone.utc), now), (0, 0))


if __name__ == "__main__":
    unittest.main()
