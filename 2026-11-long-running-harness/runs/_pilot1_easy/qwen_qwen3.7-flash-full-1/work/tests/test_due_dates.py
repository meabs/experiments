"""Tests for tasks.py - Feature F07: due dates."""
import json
import os
import subprocess
import tempfile
import shutil
import unittest


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(_SCRIPT_DIR, "..", "tasks.py")


def run_task(args, cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    cmd = ["python3", SCRIPT_PATH] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF07DueDates(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_with_due_shows_suffix(self):
        """add with --due shows 'due:YYYY-MM-DD' suffix."""
        run_task(["add", "Task", "--due", "2026-03-01"], self.tmpdir)
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Task due:2026-03-01")

    def test_invalid_date_error(self):
        """Invalid date exits 1 with error message."""
        stdout, stderr, rc = run_task(["add", "Task", "--due", "2026-13-40"], self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2026-13-40", stderr)

    def test_overdue_filters_open_tasks(self):
        """--overdue shows only open tasks due before --today."""
        run_task(["add", "Past task", "--due", "2020-01-01"], self.tmpdir)
        run_task(["add", "Future task", "--due", "2099-01-01"], self.tmpdir)
        run_task(["add", "Done past", "--due", "2020-01-01"], self.tmpdir)
        run_task(["done", "3"], self.tmpdir)
        stdout, _, _ = run_task(["list", "--overdue", "--today", "2024-01-01"], self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("Past task", lines[0])

    def test_suffix_order_priority_tags_due(self):
        """Suffix order: priority, then tags, then due."""
        run_task(["add", "Task", "--priority", "low", "--tag", "t", "--due", "2026-03-01"], self.tmpdir)
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Task (low) #t due:2026-03-01")


if __name__ == "__main__":
    unittest.main()
