#!/usr/bin/env python3
"""Tests for tasks.py."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


class TaskManagerTest(unittest.TestCase):
    """Base test class that runs commands in a temp directory."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_file = os.path.join(self.tmpdir, "tasks.json")

    def run_cmd(self, *args):
        """Run tasks.py with given args and return (stdout, stderr, returncode)."""
        cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args)
        result = subprocess.run(
            cmd, cwd=self.tmpdir, capture_output=True, text=True
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    # F01: add
    def test_add_creates_task(self):
        stdout, stderr, rc = self.run_cmd("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")
        self.assertTrue(os.path.exists(self.tasks_file))

    def test_add_second_task(self):
        self.run_cmd("add", "Buy milk")
        stdout, stderr, rc = self.run_cmd("add", "Walk dog")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    # F02: list
    def test_list_empty(self):
        stdout, stderr, rc = self.run_cmd("list")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_two_tasks(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        stdout, stderr, rc = self.run_cmd("list")
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    # F03: done
    def test_done_marks_task(self):
        self.run_cmd("add", "Buy milk")
        stdout, stderr, rc = self.run_cmd("done", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")

    def test_done_shows_in_list(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("done", "1")
        stdout, _, _ = self.run_cmd("list")
        self.assertIn("[x] Buy milk", stdout)

    def test_done_unknown_id(self):
        stdout, stderr, rc = self.run_cmd("done", "9")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", stderr)

    # F04: delete
    def test_delete_removes_task(self):
        self.run_cmd("add", "Buy milk")
        stdout, _, rc = self.run_cmd("delete", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Deleted 1")

    def test_delete_next_id_not_reused(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("delete", "1")
        stdout, _, rc = self.run_cmd("add", "Walk dog")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    def test_delete_unknown_id(self):
        stdout, stderr, rc = self.run_cmd("delete", "9")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", stderr)

    # F05: priority
    def test_add_high_priority(self):
        self.run_cmd("add", "a", "--priority", "high")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] a (high)")

    def test_add_low_priority(self):
        self.run_cmd("add", "a", "--priority", "low")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] a (low)")

    def test_default_priority_no_suffix(self):
        self.run_cmd("add", "a")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] a")

    def test_invalid_priority(self):
        stdout, stderr, rc = self.run_cmd("add", "a", "--priority", "urgent")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid priority: urgent", stderr)

    def test_sort_by_priority(self):
        self.run_cmd("add", "c", "--priority", "low")
        self.run_cmd("add", "b", "--priority", "high")
        self.run_cmd("add", "a", "--priority", "medium")
        stdout, _, _ = self.run_cmd("list", "--sort", "priority")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("(high)", lines[0])
        # medium has no suffix, just the title
        self.assertIn("[ ] a", lines[1])
        self.assertIn("(low)", lines[2])

    # F06: tags
    def test_add_tags(self):
        self.run_cmd("add", "a", "--tag", "work", "--tag", "home")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] a #work #home")

    def test_filter_by_tag(self):
        self.run_cmd("add", "a", "--tag", "work")
        self.run_cmd("add", "b", "--tag", "home")
        stdout, _, _ = self.run_cmd("list", "--tag", "work")
        self.assertEqual(stdout, "1 [ ] a #work")

    # F07: due dates
    def test_add_due_date(self):
        self.run_cmd("add", "a", "--due", "2026-03-01")
        stdout, _, _ = self.run_cmd("list")
        self.assertIn("due:2026-03-01", stdout)

    def test_invalid_date(self):
        stdout, stderr, rc = self.run_cmd("add", "a", "--due", "2026-13-40")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2026-13-40", stderr)

    def test_overdue(self):
        self.run_cmd("add", "a", "--due", "2020-01-01")
        stdout, _, _ = self.run_cmd("list", "--overdue", "--today", "2026-01-01")
        self.assertNotEqual(stdout, "No tasks")

    def test_overdue_excludes_done(self):
        self.run_cmd("add", "a", "--due", "2020-01-01")
        self.run_cmd("done", "1")
        stdout, _, _ = self.run_cmd("list", "--overdue", "--today", "2026-01-01")
        # Done tasks should not appear in overdue
        self.assertNotIn("[ ]", stdout)

    def test_suffix_order_priority_tags_due(self):
        """Verify suffix order: priority, tags, due date."""
        self.run_cmd("add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] a (low) #t due:2026-03-01")


    # F08: edit
    def test_edit_title(self):
        self.run_cmd("add", "old title")
        stdout, _, rc = self.run_cmd("edit", "1", "--title", "new title")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Edited 1")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] new title")

    def test_edit_unknown_id(self):
        stdout, stderr, rc = self.run_cmd("edit", "9", "--title", "x")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", stderr)

    # F09: search
    def test_search_case_insensitive(self):
        self.run_cmd("add", "Buy Milk")
        stdout, _, _ = self.run_cmd("search", "milk")
        self.assertIn("Buy Milk", stdout)

    def test_search_no_match(self):
        self.run_cmd("add", "Buy Milk")
        stdout, _, _ = self.run_cmd("search", "xyz")
        self.assertEqual(stdout, "No matches")

    # F10: export
    def test_export_json(self):
        self.run_cmd("add", "a")
        stdout, _, _ = self.run_cmd("export", "--format", "json")
        data = json.loads(stdout)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["title"], "a")
        self.assertTrue(isinstance(data[0]["done"], bool))

    def test_export_csv(self):
        self.run_cmd("add", "a")
        stdout, _, _ = self.run_cmd("export", "--format", "csv")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertEqual(lines[1], "1,a,false,medium,,")

    def test_export_empty(self):
        stdout, _, _ = self.run_cmd("export", "--format", "json")
        self.assertEqual(stdout, "[]")

    # F11: stats
    def test_stats_empty(self):
        stdout, _, _ = self.run_cmd("stats")
        self.assertEqual(stdout, "open: 0\ndone: 0\ntotal: 0")

    def test_stats_counts(self):
        self.run_cmd("add", "task1")
        self.run_cmd("add", "task2")
        self.run_cmd("done", "1")
        stdout, _, _ = self.run_cmd("stats")
        self.assertEqual(stdout, "open: 1\ndone: 1\ntotal: 2")

    # F12: undo
    def test_undo_after_add(self):
        self.run_cmd("add", "Buy milk")
        stdout, _, rc = self.run_cmd("undo")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Undone")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "No tasks")

    def test_undo_reuses_id(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("undo")
        stdout, _, _ = self.run_cmd("add", "Walk dog")
        self.assertEqual(stdout, "Added 1")

    def test_nothing_to_undo(self):
        stdout, stderr, rc = self.run_cmd("undo")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "Nothing to undo")

    def test_undo_across_runs(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("undo")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "No tasks")


if __name__ == "__main__":
    unittest.main()
