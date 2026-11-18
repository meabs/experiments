#!/usr/bin/env python3
"""Tests for F07: due dates feature."""

import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestDueDates(unittest.TestCase):
    """F07: due dates --due YYYY-MM-DD, suffix display, invalid error, list --overdue."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PY, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_add_with_due_shows_suffix(self):
        """list shows '1 [ ] a (low) #t due:2026-03-01'"""
        r = self._run("add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a (low) #t due:2026-03-01")

    def test_invalid_date_error(self):
        """--due 2026-13-40 exits 1 with 'Invalid date: 2026-13-40'"""
        r = self._run("add", "a", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)

    def test_invalid_date_another(self):
        """--due with bad format also errors"""
        r = self._run("add", "a", "--due", "not-a-date")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: not-a-date", r.stderr)

    def test_overdue_shows_only_open_tasks_before_today(self):
        """--overdue shows only OPEN tasks due before --today"""
        # Add an overdue task
        self._run("add", "overdue task", "--due", "2020-01-01")
        # Add a future task
        self._run("add", "future task", "--due", "2099-12-31")
        # Add a done task with past due date (should NOT show as overdue)
        self._run("add", "done overdue", "--due", "2020-01-01")
        self._run("done", "3")
        # Check overdue with fixed today
        r = self._run("list", "--overdue", "--today", "2025-01-01")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("overdue task", lines[0])
        self.assertNotIn("future task", lines[0])
        self.assertNotIn("done overdue", lines[0])

    def test_no_overdue_tasks(self):
        """list --overdue with no overdue tasks prints No tasks"""
        self._run("add", "future task", "--due", "2099-12-31")
        r = self._run("list", "--overdue", "--today", "2025-01-01")
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_task_without_due_has_no_suffix(self):
        """task without due date has no due suffix"""
        r = self._run("add", "no due task")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] no due task")

    def test_due_date_persists_across_runs(self):
        """due date persists across separate runs"""
        self._run("add", "persistent task", "--due", "2025-06-15")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertIn("due:2025-06-15", lines[0])

    def test_done_task_not_shown_as_overdue(self):
        """done tasks should not appear in --overdue even if due is in the past"""
        self._run("add", "old done", "--due", "2020-01-01")
        self._run("done", "1")
        r = self._run("list", "--overdue", "--today", "2025-01-01")
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_overdue_default_today(self):
        """--overdue without --today uses real date"""
        # Use a clearly past date that would be overdue regardless of today
        self._run("add", "very old", "--due", "2000-01-01")
        r = self._run("list", "--overdue")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("very old", lines[0])


if __name__ == "__main__":
    unittest.main()
