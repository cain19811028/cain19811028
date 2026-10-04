import re
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from helpers import page, repo
from readmegen import cards, config, github

SVG = "{http://www.w3.org/2000/svg}"
NOW = datetime(2026, 10, 4, tzinfo=timezone.utc)


def sample_stats(**page_args):
    defaults = dict(
        repos=[
            repo("a&b <tool>", stars=3, langs=[("Python", 900, "#3572A5"), ("Go", 100, "#00ADD8")])
        ],
        counts=[1, 0, 3, 4, 2, 0, 1] * 10,
    )
    defaults.update(page_args)
    return github.summarize([page(**defaults)])


def all_cards(stats):
    return {
        "hero": cards.hero(stats, NOW),
        "stats": cards.stats_card(stats),
        "languages": cards.languages_card(stats),
        "activity": cards.activity_card(stats),
    }


def text_of(svg):
    """Visible text: the content of every <text>, in document order."""
    return "".join("".join(t.itertext()) for t in ET.fromstring(svg).iter(f"{SVG}text"))


class EveryCardTest(unittest.TestCase):
    def test_cards_are_self_contained_svg(self):
        for name, svg in all_cards(sample_stats()).items():
            with self.subTest(name):
                root = ET.fromstring(svg)
                tags = {el.tag.removeprefix(SVG) for el in root.iter()}
                self.assertFalse(tags & {"script", "image", "foreignObject", "use"})
                self.assertNotIn("http", svg.replace('xmlns="http://www.w3.org/2000/svg"', ""))

    def test_motion_stops_for_reduced_motion(self):
        for name, svg in all_cards(sample_stats()).items():
            with self.subTest(name):
                self.assertIn("@media (prefers-reduced-motion:reduce)", svg)

    def test_names_from_github_are_escaped(self):
        hero = cards.hero(sample_stats(), NOW)
        self.assertIn("a&b <tool>", text_of(hero))


class HeroTest(unittest.TestCase):
    def test_version_is_years_and_months_on_github(self):
        # The fixture user joined on 2012-03-07; NOW is 2026-10-04.
        self.assertIn("u v14.6", text_of(cards.hero(sample_stats(), NOW)))

    def test_exactly_one_prompt_is_visible_at_any_time(self):
        svg = cards.hero(sample_stats(), NOW)
        stops = {
            int(i): [(float(p), int(o)) for p, o in re.findall(r"([\d.]+)%\{opacity:(\d)\}", body)]
            for i, body in re.findall(r"@keyframes pr(\d+)\{((?:[\d.]+%\{opacity:\d\})+)\}", svg)
        }
        self.assertEqual(len(stops), len(config.PROMPTS))
        for pct in [i / 10 for i in range(1000)]:
            # step-end: each stop holds until the next one.
            shown = [i for i, s in stops.items() if [o for p, o in s if p <= pct][-1]]
            self.assertEqual(len(shown), 1, f"{pct}%: prompts {shown}")

    def test_prompts_fill_in_years(self):
        self.assertIn("summarize my 14 years on GitHub", text_of(cards.hero(sample_stats(), NOW)))


class ActivityTest(unittest.TestCase):
    def test_one_cell_per_day_and_no_two_days_share_a_cell(self):
        stats = sample_stats()
        root = ET.fromstring(cards.activity_card(stats))
        cells = [
            (rect.get("x"), rect.get("y"))
            for group in root.iter(f"{SVG}g")
            if group.get("class") == "pop"
            for rect in group.iter(f"{SVG}rect")
        ]
        self.assertEqual(len(cells), len(stats.days))
        self.assertEqual(len(set(cells)), len(cells))

    def test_summary_shows_streaks(self):
        text = text_of(cards.activity_card(sample_stats(counts=[0, 2, 2, 0, 3, 3, 3])))
        self.assertIn("current streak 3d", text)
        self.assertIn("longest streak 3d", text)


class LanguagesTest(unittest.TestCase):
    def test_long_tail_is_grouped_as_other(self):
        langs = [(f"L{i}", 10 - i, "#000000") for i in range(10)]
        text = text_of(cards.languages_card(sample_stats(repos=[repo("x", langs=langs)]), limit=3))
        self.assertIn("Other", text)
        self.assertNotIn("L3", text)


if __name__ == "__main__":
    unittest.main()
