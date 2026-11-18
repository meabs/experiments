#!/usr/bin/env python3
"""Tests for F07: due dates."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestDueDates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py into the temp dir
        shutil.copy("tasks.py", self.tmpdir)
        self.tasks_file = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        """Run tasks.py with given args in the temp directory."""
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
        )
        return result

    def _load_tasks(self):
        with open(self.tasks_file) as f:
            return json.load(f)

    def test_add_with_due_date(self):
        """add with --due sets the due date."""
        r = self._run("add", "Buy milk", "--due", "2026-03-01")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        data = self._load_tasks()
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["due"], "2026-03-01")

    def test_list_shows_due_suffix(self):
        """list shows the due:YYYY-MM-DD suffix."""
        self._run("add", "Buy milk", "--due", "2026-03-01")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("due:2026-03-01", lines[0])

    def test_list_due_with_priority_and_tags(self):
        """Suffix order: priority, then tags, then due date."""
        self._run("add", "Task", "--priority", "low", "--tag", "work", "--due", "2026-03-01")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        line = r.stdout.strip()
        # Check order: (low) #work due:2026-03-01
        low_pos = line.find("(low)")
        tag_pos = line.find("#work")
        due_pos = line.find("due:2026-03-01")
        self.assertLess(low_pos, tag_pos)
        self.assertLess(tag_pos, due_pos)

    def test_invalid_date_error(self):
        """Invalid date prints error to stderr and exits 1."""
        r = self._run("add", "Bad date", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)

    def test_overdue_filters_open_tasks(self):
        """--overdue shows only open tasks with due date before --today."""
        self._run("add", "Past task", "--due", "2020-01-01")
        self._run("add", "Future task", "--due", "2099-01-01")
        self._run("add", "No due date", "--due", "2024-06-01")
        # Mark first as done
        self._run("done", "1")

        r = self._run("list", "--overdue", "--today", "2025-01-01")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        # Only task 3 should be overdue (open, due before 2025-01-01)
        self.assertEqual(len(lines), 1)
        self.assertIn("No due date", lines[0])

    def test_overdue_no_matches(self):
        """--overdue with no matches prints 'No tasks'."""
        self._run("add", "Future task", "--due", "2099-01-01")
        r = self._run("list", "--overdue", "--today", "2025-01-01")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_done_task_not_overdue(self):
        """Done tasks are not shown as overdue."""
        self._run("add", "Past task", "--due", "2020-01-01")
        self._run("done", "1")
        r = self._run("list", "--overdue", "--today", "2025-01-01")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_default_today_for_overdue(self):
        """When --today is not given, use current date."""
        # This test depends on current date; we'll just check it doesn't crash
        self._run("add", "Some task", "--due", "2020-01-01")
        r = self._run("list", "--overdue")
        self.assertEqual(r.returncode, 0)

    def test_invalid_date_variations(self):
        """Test various invalid date formats."""
        for bad_date in ["2026-02-30", "not-a-date", "", "2026/01/01"]:
            r = self._run("add", "Task", "--due", bad_date)
            self.assertEqual(r.returncode, 1, f"Expected error for date '{bad_date}'")
            self.assertIn("Invalid date:", r.stderr, f"Expected error message for '{bad_date}'")

    def test_list_without_due_date(self):
        """Tasks without a due date don't show the suffix."""
        self._run("add", "No due task")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertNotIn("due:", lines[0])


if __name__ == "__main__":
    unittest.main()
