import io
import unittest
import urllib.error
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from datetime import datetime, timezone
from unittest import mock

from helpers import page  # first: it puts scripts/ on sys.path

# isort: split
import build_profile
from readmegen import github, views

SVG = "{http://www.w3.org/2000/svg}"
NOW = datetime(2026, 10, 4, tzinfo=timezone.utc)


def komarev_badge(message):
    """Shaped like komarev's reply: every text twice, its shadow first."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="103.5" height="20">
    <g fill="#fff" text-anchor="middle" font-size="11">
        <text x="40.8" y="15" fill="#010101" fill-opacity=".3">profile views</text>
        <text x="40.8" y="14">profile views</text>
        <text x="90.5" y="15" fill="#010101" fill-opacity=".3">{message}</text>
        <text x="90.5" y="14">{message}</text>
    </g>
</svg>"""


class ParseCountTest(unittest.TestCase):
    def test_reads_the_number_on_the_badge(self):
        self.assertEqual(views.parse_count(komarev_badge("44")), 44)
        self.assertEqual(views.parse_count(komarev_badge("1,234,567")), 1234567)

    def test_an_error_badge_is_not_a_count(self):
        with self.assertRaises(ValueError):
            views.parse_count(komarev_badge("The maximum number of views has been reached"))

    def test_a_reply_that_is_not_svg_is_not_a_count(self):
        with self.assertRaises(ValueError):
            views.parse_count("<html><body>502 Bad Gateway</body>")


class BadgeTest(unittest.TestCase):
    def test_is_self_contained_svg(self):
        svg = views.badge(1234)
        tags = {el.tag.removeprefix(SVG) for el in ET.fromstring(svg).iter()}
        self.assertFalse(tags & {"script", "image", "foreignObject", "use"})
        self.assertNotIn("http", svg.replace('xmlns="http://www.w3.org/2000/svg"', ""))

    def test_shows_the_count_with_thousands_grouped(self):
        root = ET.fromstring(views.badge(1234567))
        self.assertEqual(root.get("aria-label"), "profile views: 1,234,567")
        self.assertEqual([t.text for t in root.iter(f"{SVG}text")], ["profile views", "1,234,567"])

    def test_is_as_wide_as_the_shields_badge_it_sits_next_to(self):
        # Widths of img.shields.io/badge/profile%20views-<count>-D97757?style=flat-square
        for count, width in ((44, 102), (1234, 120), (99999, 128)):
            with self.subTest(count):
                self.assertEqual(ET.fromstring(views.badge(count)).get("width"), str(width))

    def test_the_count_fits_its_box(self):
        for count in (0, 7, 44, 1234, 10**12):
            with self.subTest(count):
                root = ET.fromstring(views.badge(count))
                label_box, count_box = root.iter(f"{SVG}rect")
                text = list(root.iter(f"{SVG}text"))[-1]
                widths = int(label_box.get("width")) + int(count_box.get("width"))
                self.assertEqual(int(root.get("width")), widths)
                self.assertGreater(int(count_box.get("width")), int(text.get("textLength")))


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.stats = github.summarize([page(counts=[1] * 7)])
        self.readme = build_profile.README.read_text(encoding="utf-8")

    def build_with_counter(self, **fetch):
        out = io.StringIO()
        with mock.patch.object(views, "fetch_count", **fetch), redirect_stdout(out):
            count = build_profile.read_view_count()
        outputs = build_profile.build(self.stats, NOW, self.readme, count)
        return outputs, out.getvalue()

    def test_the_badge_shows_the_live_count(self):
        outputs, _ = self.build_with_counter(return_value=44)
        self.assertIn("profile views: 44", outputs[build_profile.ASSETS / "views.svg"])

    def test_an_unreadable_counter_keeps_the_last_badge_and_says_so(self):
        failures = [
            urllib.error.URLError("timed out"),
            TimeoutError("read timed out"),
            ValueError("counter badge shows no count"),
        ]
        for failure in failures:
            with self.subTest(type(failure).__name__):
                outputs, out = self.build_with_counter(side_effect=failure)
                self.assertNotIn(build_profile.ASSETS / "views.svg", outputs)
                self.assertIn(build_profile.ASSETS / "stats.svg", outputs)
                self.assertIn("::warning::", out)


if __name__ == "__main__":
    unittest.main()
