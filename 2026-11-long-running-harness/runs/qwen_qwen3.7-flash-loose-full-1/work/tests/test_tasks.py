#!/usr/bin/env python3
"""Tests for tasks.py."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tasks.py")


def run_tasks(*args, cwd=None):
    """Run tasks.py with given args and return (stdout, stderr, returncode)."""
    if cwd is None:
        cwd = os.getcwd()
    env = os.environ.copy()
    result = subprocess.run(
        ["python3", TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=cwd, env=env
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py into the temp dir
        shutil.copy2(TASKS_PY, os.path.join(self.tmpdir, "tasks.py"))
        # Clean up any existing files
        for f in ["tasks.json", "undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)

    def run_tasks(self, *args):
        return run_tasks(*args, cwd=self.tmpdir)


class TestAdd(BaseTest):
    """Feature F01: add command."""

    def test_add_single_task(self):
        stdout, stderr, rc = self.run_tasks("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_add_second_task(self):
        self.run_tasks("add", "Buy milk")
        stdout, stderr, rc = self.run_tasks("add", "Walk dog")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")


class TestList(BaseTest):
    """Feature F02: list command."""

    def test_empty_list(self):
        stdout, stderr, rc = self.run_tasks("list")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_two_tasks(self):
        self.run_tasks("add", "Buy milk")
        self.run_tasks("add", "Walk dog")
        stdout, stderr, rc = self.run_tasks("list")
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


class TestDone(BaseTest):
    """Feature F03: done command."""

    def test_done_task(self):
        self.run_tasks("add", "Buy milk")
        stdout, stderr, rc = self.run_tasks("done", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")

    def test_done_shows_in_list(self):
        self.run_tasks("add", "Buy milk")
        self.run_tasks("done", "1")
        stdout, stderr, rc = self.run_tasks("list")
        self.assertIn("1 [x] Buy milk", stdout)

    def test_done_unknown_id(self):
        stdout, stderr, rc = self.run_tasks("done", "99")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)


class TestDelete(BaseTest):
    """Feature F04: delete command."""

    def test_delete_task(self):
        self.run_tasks("add", "Buy milk")
        self.run_tasks("add", "Walk dog")
        stdout, stderr, rc = self.run_tasks("delete", "2")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Deleted 2")

    def test_delete_next_id_not_reused(self):
        self.run_tasks("add", "Task 1")
        self.run_tasks("add", "Task 2")
        self.run_tasks("delete", "2")
        stdout, stderr, rc = self.run_tasks("add", "Task 3")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 3")

    def test_delete_unknown_id(self):
        stdout, stderr, rc = self.run_tasks("delete", "99")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)


class TestPriority(BaseTest):
    """Feature F05: priority."""

    def test_add_high_priority(self):
        self.run_tasks("add", "Urgent task", "--priority", "high")
        stdout, stderr, rc = self.run_tasks("list")
        self.assertIn("(high)", stdout)

    def test_add_low_priority(self):
        self.run_tasks("add", "Low task", "--priority", "low")
        stdout, stderr, rc = self.run_tasks("list")
        self.assertIn("(low)", stdout)

    def test_default_is_medium_no_suffix(self):
        self.run_tasks("add", "Normal task")
        stdout, stderr, rc = self.run_tasks("list")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertNotIn("(", lines[0])

    def test_invalid_priority(self):
        stdout, stderr, rc = self.run_tasks("add", "Task", "--priority", "urgent")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid priority: urgent", stderr)

    def test_sort_by_priority(self):
        self.run_tasks("add", "Low", "--priority", "low")
        self.run_tasks("add", "High", "--priority", "high")
        self.run_tasks("add", "Medium", "--priority", "medium")
        stdout, stderr, rc = self.run_tasks("list", "--sort", "priority")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("(high)", lines[0])
        self.assertNotIn("(", lines[1])
        self.assertIn("(low)", lines[2])


class TestTags(BaseTest):
    """Feature F06: tags."""

    def test_add_with_tags(self):
        self.run_tasks("add", "Work home task", "--tag", "work", "--tag", "home")
        stdout, stderr, rc = self.run_tasks("list")
        self.assertIn("#work #home", stdout)

    def test_filter_by_tag(self):
        self.run_tasks("add", "Work task", "--tag", "work")
        self.run_tasks("add", "Home task", "--tag", "home")
        stdout, stderr, rc = self.run_tasks("list", "--tag", "work")
        self.assertIn("Work task", stdout)
        self.assertNotIn("Home task", stdout)

    def test_tag_order_preserved(self):
        self.run_tasks("add", "Multi tag", "--tag", "beta", "--tag", "alpha")
        stdout, stderr, rc = self.run_tasks("list")
        self.assertIn("#beta #alpha", stdout)


class TestDueDates(BaseTest):
    """Feature F07: due dates."""

    def test_add_with_due_date(self):
        self.run_tasks("add", "Due task", "--due", "2026-12-31")
        stdout, stderr, rc = self.run_tasks("list")
        self.assertIn("due:2026-12-31", stdout)

    def test_invalid_date(self):
        stdout, stderr, rc = self.run_tasks("add", "Task", "--due", "2026-13-40")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2026-13-40", stderr)

    def test_overdue_filter(self):
        self.run_tasks("add", "Past due", "--due", "2020-01-01")
        self.run_tasks("add", "Future due", "--due", "2099-12-31")
        stdout, stderr, rc = self.run_tasks("list", "--overdue", "--today", "2024-06-15")
        self.assertIn("Past due", stdout)
        self.assertNotIn("Future due", stdout)


class TestEdit(BaseTest):
    """Feature F08: edit command."""

    def test_edit_title(self):
        self.run_tasks("add", "Old title")
        stdout, stderr, rc = self.run_tasks("edit", "1", "--title", "New title")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Edited 1")

    def test_edit_shows_new_title(self):
        self.run_tasks("add", "Old title")
        self.run_tasks("edit", "1", "--title", "New title")
        stdout, stderr, rc = self.run_tasks("list")
        self.assertIn("New title", stdout)

    def test_edit_unknown_id(self):
        stdout, stderr, rc = self.run_tasks("edit", "99", "--title", "New")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)


class TestSearch(BaseTest):
    """Feature F09: search command."""

    def test_search_case_insensitive(self):
        self.run_tasks("add", "Buy Milk")
        self.run_tasks("add", "milkshake")
        stdout, stderr, rc = self.run_tasks("search", "milk")
        self.assertIn("Buy Milk", stdout)
        self.assertIn("milkshake", stdout)

    def test_search_no_match(self):
        self.run_tasks("add", "Buy milk")
        stdout, stderr, rc = self.run_tasks("search", "xyz")
        self.assertEqual(stdout, "No matches")


class TestExport(BaseTest):
    """Feature F10: export command."""

    def test_export_json(self):
        self.run_tasks("add", "Test task")
        stdout, stderr, rc = self.run_tasks("export", "--format", "json")
        data = json.loads(stdout)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["title"], "Test task")
        self.assertFalse(data[0]["done"])

    def test_export_csv(self):
        self.run_tasks("add", "Test task")
        stdout, stderr, rc = self.run_tasks("export", "--format", "csv")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertIn("Test task", lines[1])

    def test_export_empty(self):
        stdout, stderr, rc = self.run_tasks("export", "--format", "json")
        data = json.loads(stdout)
        self.assertEqual(data, [])


class TestStats(BaseTest):
    """Feature F11: stats command."""

    def test_stats_zeros(self):
        stdout, stderr, rc = self.run_tasks("stats")
        self.assertEqual(stdout, "open: 0\ndone: 0\ntotal: 0")

    def test_stats_counts(self):
        self.run_tasks("add", "Task 1")
        self.run_tasks("add", "Task 2")
        self.run_tasks("done", "1")
        stdout, stderr, rc = self.run_tasks("stats")
        self.assertIn("open: 1", stdout)
        self.assertIn("done: 1", stdout)
        self.assertIn("total: 2", stdout)


class TestUndo(BaseTest):
    """Feature F12: undo command."""

    def test_undo_after_add(self):
        self.run_tasks("add", "Task 1")
        stdout, stderr, rc = self.run_tasks("undo")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Undone")
        # Task should be gone, next add should get id 1 again
        stdout, stderr, rc = self.run_tasks("add", "Task A")
        self.assertEqual(stdout, "Added 1")

    def test_undo_nothing_to_undo(self):
        stdout, stderr, rc = self.run_tasks("undo")
        self.assertEqual(rc, 1)
        self.assertIn("Nothing to undo", stderr)

    def test_undo_multiple(self):
        self.run_tasks("add", "Task 1")
        self.run_tasks("add", "Task 2")
        self.run_tasks("undo")
        self.run_tasks("undo")
        stdout, stderr, rc = self.run_tasks("list")
        self.assertEqual(stdout, "No tasks")


if __name__ == "__main__":
    unittest.main()
