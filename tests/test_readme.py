import unittest
from html.parser import HTMLParser
from pathlib import Path

from readmegen import readme, views
from readmegen.github import Repo

ROOT = Path(__file__).resolve().parent.parent
DOC = f"intro\n{readme.START}\nold table\n{readme.END}\noutro\n"


class _Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.found.append(dict(attrs))


def readme_images():
    """The attributes of every <img> in the committed README."""
    parser = _Images()
    parser.feed((ROOT / "README.md").read_text(encoding="utf-8"))
    return parser.found


class ReplaceBlockTest(unittest.TestCase):
    def test_only_the_marked_block_changes(self):
        updated = readme.replace_block(DOC, "new table")
        self.assertEqual(updated, f"intro\n{readme.START}\nnew table\n{readme.END}\noutro\n")

    def test_running_twice_changes_nothing(self):
        once = readme.replace_block(DOC, "t")
        self.assertEqual(readme.replace_block(once, "t"), once)

    def test_missing_markers_are_an_error(self):
        with self.assertRaises(ValueError):
            readme.replace_block("no markers here", "t")


class ProjectsTableTest(unittest.TestCase):
    def test_cells_cannot_break_the_table(self):
        table = readme.projects_table([Repo("x", "a | b\nc", "https://github.com/u/x", 3, None)])
        row = table.splitlines()[2]
        self.assertEqual(row.count(" | "), 3)
        self.assertIn("a \\| b c", row)
        self.assertIn("| — |", row)


class CommittedReadmeTest(unittest.TestCase):
    # The workflow rewrites the real README, so a redesign that drops the markers breaks CI.
    def test_has_a_slot_for_the_projects_table(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        table = readme.projects_table([Repo("x", None, "https://github.com/u/x", 0, None)])
        self.assertIn(table, readme.replace_block(text, table))

    def test_every_local_image_is_committed(self):
        for src in (img["src"] for img in readme_images() if "://" not in img["src"]):
            with self.subTest(src):
                self.assertTrue((ROOT / src).is_file())

    def test_the_live_view_counter_is_an_invisible_pixel(self):
        # komarev can't be cached, so GitHub fetches it live on every visit and shows a broken
        # image whenever that fetch fails. Only a pixel nobody sees may depend on it.
        counters = [img for img in readme_images() if img["src"].startswith(views.COUNTER)]
        self.assertTrue(counters, "nothing counts profile views any more")
        for img in counters:
            self.assertIn("style=pixel", img["src"])
            self.assertEqual((img.get("width"), img.get("height"), img.get("alt")), ("1", "1", ""))


if __name__ == "__main__":
    unittest.main()
