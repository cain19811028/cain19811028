import unittest
from pathlib import Path

from readmegen import readme
from readmegen.github import Repo

DOC = f"intro\n{readme.START}\nold table\n{readme.END}\noutro\n"


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
        text = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
        table = readme.projects_table([Repo("x", None, "https://github.com/u/x", 0, None)])
        self.assertIn(table, readme.replace_block(text, table))


if __name__ == "__main__":
    unittest.main()
