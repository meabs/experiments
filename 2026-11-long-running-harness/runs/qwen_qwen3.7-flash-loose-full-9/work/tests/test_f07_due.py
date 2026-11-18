"""Tests for F07: due dates feature."""
import json
import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_tasks_in(tmpdir, *args):
    """Run tasks.py with given args in tmpdir, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=tmpdir
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestF07DueDates(unittest.TestCase):

    def test_add_with_due_date(self):
        """add TITLE --due YYYY-MM-DD creates task with due date."""
        tmpdir = tempfile.mkdtemp()
        rc, out, _ = run_tasks_in(tmpdir, "add", "Task", "--due", "2025-06-15")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 1")

    def test_due_date_shown_in_list(self):
        """list shows '1 [ ] a due:YYYY-MM-DD'."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "a", "--due", "2025-06-15")
        rc, out, _ = run_tasks_in(tmpdir, "list")
        self.assertIn("due:2025-06-15", out)

    def test_full_task_line_with_priority_tags_and_due(self):
        """list shows full line with priority, tags, and due date suffix."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "a", "--priority", "low", "--tag", "t", "--due", "2025-03-01")
        rc, out, _ = run_tasks_in(tmpdir, "list")
        # Expected format: "1 [ ] a (low) #t due:2025-03-01"
        expected = "1 [ ] a (low) #t due:2025-03-01"
        self.assertEqual(out, expected)

    def test_invalid_date_rejected(self):
        """--due 2026-13-40 exits 1 with 'Invalid date: 2026-13-40'."""
        tmpdir = tempfile.mkdtemp()
        rc, _, err = run_tasks_in(tmpdir, "add", "Task", "--due", "2026-13-40")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2026-13-40", err)

    def test_invalid_date_bad_month(self):
        """--due 2025-00-15 exits 1."""
        tmpdir = tempfile.mkdtemp()
        rc, _, err = run_tasks_in(tmpdir, "add", "Task", "--due", "2025-00-15")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2025-00-15", err)

    def test_invalid_date_bad_day_for_month(self):
        """--due 2025-02-30 exits 1 (Feb has no 30th)."""
        tmpdir = tempfile.mkdtemp()
        rc, _, err = run_tasks_in(tmpdir, "add", "Task", "--due", "2025-02-30")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2025-02-30", err)

    def test_invalid_date_wrong_format(self):
        """--due 2025/06/15 exits 1."""
        tmpdir = tempfile.mkdtemp()
        rc, _, err = run_tasks_in(tmpdir, "add", "Task", "--due", "2025/06/15")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2025/06/15", err)

    def test_overdue_no_today_defaults_to_now(self):
        """--overdue without --today defaults to real date."""
        tmpdir = tempfile.mkdtemp()
        # Add a task due yesterday (in the past)
        import datetime
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        run_tasks_in(tmpdir, "add", "Overdue task", "--due", yesterday)
        # Add a task due tomorrow (in the future)
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        run_tasks_in(tmpdir, "add", "Future task", "--due", tomorrow)
        # Only overdue task should show
        rc, out, _ = run_tasks_in(tmpdir, "list", "--overdue")
        self.assertIn("Overdue task", out)
        self.assertNotIn("Future task", out)

    def test_overdue_with_today(self):
        """--overdue --today DATE shows only tasks due before DATE."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "Past task", "--due", "2020-01-01")
        run_tasks_in(tmpdir, "add", "Future task", "--due", "2030-01-01")
        rc, out, _ = run_tasks_in(tmpdir, "list", "--overdue", "--today", "2025-06-15")
        self.assertIn("Past task", out)
        self.assertNotIn("Future task", out)

    def test_overdue_excludes_done_tasks(self):
        """--overdue shows only OPEN tasks whose due date is before --today."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "Overdue but done", "--due", "2020-01-01")
        run_tasks_in(tmpdir, "done", "1")
        run_tasks_in(tmpdir, "add", "Overdue still open", "--due", "2020-01-01")
        rc, out, _ = run_tasks_in(tmpdir, "list", "--overdue", "--today", "2025-06-15")
        self.assertIn("Overdue still open", out)
        self.assertNotIn("Overdue but done", out)

    def test_overdue_no_overdue_tasks(self):
        """--overdue when nothing is overdue prints No tasks."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "Future task", "--due", "2030-01-01")
        rc, out, _ = run_tasks_in(tmpdir, "list", "--overdue", "--today", "2025-06-15")
        self.assertIn("No tasks", out)

    def test_overdue_only_open_tasks_counted(self):
        """--overdue does not include tasks without due dates."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "No due date")
        rc, out, _ = run_tasks_in(tmpdir, "list", "--overdue", "--today", "2025-06-15")
        self.assertIn("No tasks", out)

    def test_stored_in_json(self):
        """Due date stored correctly in tasks.json."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "Task", "--due", "2025-06-15")
        with open(os.path.join(tmpdir, "tasks.json")) as f:
            data = json.load(f)
        task = data["tasks"]["1"]
        self.assertEqual(task["due"], "2025-06-15")

    def test_leap_year_valid(self):
        """--due 2024-02-29 is valid (leap year)."""
        tmpdir = tempfile.mkdtemp()
        rc, _, err = run_tasks_in(tmpdir, "add", "Leap day task", "--due", "2024-02-29")
        self.assertEqual(rc, 0)

    def test_leap_year_invalid(self):
        """--due 2023-02-29 is invalid (not leap year)."""
        tmpdir = tempfile.mkdtemp()
        rc, _, err = run_tasks_in(tmpdir, "add", "Task", "--due", "2023-02-29")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2023-02-29", err)


if __name__ == "__main__":
    unittest.main()
