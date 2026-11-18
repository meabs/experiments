"""Tests for feature F07: due dates."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


class TestF07DueDates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        tf = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(tf):
            os.remove(tf)

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, TASKS_PY] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def test_add_due_shows_suffix(self):
        """add with --due shows due:YYYY-MM-DD suffix."""
        out, err, rc = self._run("add", "a", "--due", "2026-03-01")
        self.assertEqual(rc, 0)
        out2, _, _ = self._run("list")
        self.assertIn("due:2026-03-01", out2)

    def test_invalid_date_error(self):
        """Invalid date exits 1 with 'Invalid date: <value>'."""
        out, err, rc = self._run("add", "a", "--due", "2026-13-40")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2026-13-40", err)

    def test_overdue_shows_only_open_tasks_before_today(self):
        """list --overdue shows only OPEN tasks due before --today."""
        # Add an overdue task (due date in the past)
        self._run("add", "old task", "--due", "2020-01-01")
        # Add a future task
        self._run("add", "future task", "--due", "2099-01-01")
        # Add a done task with past due date (should NOT show as overdue)
        self._run("add", "done task", "--due", "2020-01-01")
        self._run("done", "3")

        out, _, _ = self._run("list", "--overdue", "--today", "2025-01-01")
        lines = out.split("\n")
        # Only task 1 should be shown (open and overdue)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("1 "))

    def test_overdue_default_today(self):
        """--overdue without --today uses current date."""
        # Use a far future date so it's not overdue with default today
        self._run("add", "future", "--due", "2099-01-01")
        out, _, _ = self._run("list", "--overdue")
        self.assertEqual(out, "No tasks")

    def test_suffix_order_priority_tags_then_due(self):
        """Suffix order: priority, then tags, then due date."""
        out, err, rc = self._run("add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        self.assertEqual(rc, 0)
        out2, _, _ = self._run("list")
        # Verify order: (low) #t due:2026-03-01
        self.assertIn("(low) #t due:2026-03-01", out2)

    def test_no_due_no_suffix(self):
        """Tasks without --due don't get a due suffix."""
        self._run("add", "no due")
        out, _, _ = self._run("list")
        self.assertNotIn("due:", out)


if __name__ == "__main__":
    unittest.main()
