import json
import os
import subprocess
import sys
import tempfile
import unittest


def run_tasks(*args):
    """Run tasks.py with the given arguments and return stdout."""
    script = os.path.join(os.path.dirname(__file__), "..", "tasks.py")
    result = subprocess.run(
        [sys.executable, script] + list(args),
        capture_output=True,
        text=True,
    )
    return result


class TestF07DueDates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        # Clean up any leftover files
        for f in ["tasks.json", "undo.json"]:
            if os.path.exists(f):
                os.remove(f)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_with_due_date_shows_suffix(self):
        """Adding a task with --due shows 'due:YYYY-MM-DD' suffix in list."""
        r = run_tasks("add", "Buy milk", "--due", "2026-03-01")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Added 1", r.stdout)
        r = run_tasks("list")
        self.assertEqual(r.returncode, 0)
        self.assertIn("due:2026-03-01", r.stdout)

    def test_add_with_priority_and_tags_and_due(self):
        """Task with priority, tags, and due date shows all suffixes in order."""
        r = run_tasks("add", "Meeting", "--priority", "high", "--tag", "work", "--due", "2026-01-15")
        self.assertEqual(r.returncode, 0)
        r = run_tasks("list")
        self.assertEqual(r.returncode, 0)
        expected = "1 [ ] Meeting (high) #work due:2026-01-15"
        self.assertIn(expected, r.stdout)

    def test_invalid_date_rejected(self):
        """Adding a task with an invalid date exits with error."""
        r = run_tasks("add", "Bad task", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)

    def test_invalid_date_bad_format(self):
        """Adding a task with malformed date exits with error."""
        r = run_tasks("add", "Bad task", "--due", "not-a-date")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date:", r.stderr)

    def test_overdue_lists_only_open_past_due(self):
        """--overdue shows only open tasks whose due date is before --today."""
        # Add an overdue task
        run_tasks("add", "Overdue task", "--due", "2020-01-01")
        # Add a future task
        run_tasks("add", "Future task", "--due", "2099-12-31")
        # Add a done task with past due
        run_tasks("add", "Done overdue", "--due", "2020-06-01")
        run_tasks("done", "3")
        # List overdue with --today
        r = run_tasks("list", "--overdue", "--today", "2025-01-01")
        self.assertEqual(r.returncode, 0)
        lines = [l for l in r.stdout.strip().split("\n") if l]
        self.assertEqual(len(lines), 1)
        self.assertIn("Overdue task", lines[0])
        self.assertNotIn("Future task", r.stdout)
        self.assertNotIn("Done overdue", r.stdout)

    def test_no_due_task_has_no_suffix(self):
        """A task without --due does not show due: suffix."""
        run_tasks("add", "Simple task")
        r = run_tasks("list")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("due:", r.stdout)


if __name__ == "__main__":
    unittest.main()
