#!/usr/bin/env python3
"""Tests for tasks.py - Feature F07: due dates."""

import os
import subprocess
import tempfile
import unittest


class TestDueDates(unittest.TestCase):
    """Test feature F07: due dates."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        project_root = os.path.dirname(os.path.dirname(__file__))
        result = subprocess.run(
            ["python3", os.path.join(project_root, "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_with_due_date(self):
        """add with --due shows due suffix."""
        r = self._run("add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r2 = self._run("list")
        line = r2.stdout.strip().split("\n")[0]
        self.assertIn("(low)", line)
        self.assertIn("#t", line)
        self.assertIn("due:2026-03-01", line)

    def test_invalid_date(self):
        """Invalid date exits 1."""
        r = self._run("add", "a", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)

    def test_overdue_filter(self):
        """--overdue shows only open tasks due before today."""
        # Add an overdue task (past date)
        self._run("add", "overdue task", "--due", "2020-01-01")
        # Add a future task
        self._run("add", "future task", "--due", "2099-01-01")
        # Add a done task with past due date
        self._run("add", "done overdue", "--due", "2020-06-01")
        self._run("done", "3")
        
        r = self._run("list", "--overdue", "--today", "2025-01-01")
        lines = r.stdout.strip().split("\n")
        # Should only show the overdue task (task 1), not the future one or the done one
        self.assertEqual(len(lines), 1)
        self.assertIn("overdue task", lines[0])


if __name__ == "__main__":
    unittest.main()
