import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


def run_task_manager(args, cwd=None):
    """Run tasks.py with given args and return (returncode, stdout, stderr)."""
    src = os.path.join(os.path.dirname(__file__), "..", "tasks.py")
    dst = os.path.join(cwd, "tasks.py") if cwd else "tasks.py"
    # Only copy if not already there
    if not os.path.exists(dst):
        shutil.copy(src, dst)
    cmd = [sys.executable, "tasks.py"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestF07DueDates(unittest.TestCase):
    """Feature 07: due dates - --due YYYY-MM-DD, suffix 'due:YYYY-MM-DD', invalid -> error, list --overdue"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_add_with_due_shows_suffix(self):
        """add with --due shows 'due:YYYY-MM-DD' suffix after tags and priority"""
        rc, out, err = run_task_manager(
            ["add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01"], cwd=self.tmpdir
        )
        self.assertEqual(rc, 0)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(out, "1 [ ] a (low) #t due:2026-03-01")

    def test_invalid_date_exits_1(self):
        """--due 2026-13-40 exits 1 with 'Invalid date: 2026-13-40'"""
        rc, out, err = run_task_manager(["add", "x", "--due", "2026-13-40"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2026-13-40", err)

    def test_overdue_filter_only_open_tasks(self):
        """--overdue shows only OPEN tasks due before --today"""
        run_task_manager(["add", "old-task", "--due", "2020-01-01"], cwd=self.tmpdir)
        run_task_manager(["add", "future-task", "--due", "2099-12-31"], cwd=self.tmpdir)
        run_task_manager(["done", "1"], cwd=self.tmpdir)  # mark old task as done
        rc, out, err = run_task_manager(
            ["list", "--overdue", "--today", "2025-06-01"], cwd=self.tmpdir
        )
        # future-task has due 2099-12-31 which is AFTER 2025-06-01, so NOT overdue
        # old-task is done, so excluded even though it would be overdue
        self.assertEqual(out, "")

    def test_overdue_filter_shows_actual_overdue(self):
        """--overdue correctly shows tasks due before today"""
        run_task_manager(["add", "task-a", "--due", "2020-01-01"], cwd=self.tmpdir)
        run_task_manager(["add", "task-b", "--due", "2025-05-01"], cwd=self.tmpdir)
        run_task_manager(["add", "task-c", "--due", "2026-01-01"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(
            ["list", "--overdue", "--today", "2025-06-01"], cwd=self.tmpdir
        )
        lines = out.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("task-a", lines[0])
        self.assertIn("task-b", lines[1])

    def test_overdue_excludes_done_tasks(self):
        """Done tasks are never shown as overdue"""
        run_task_manager(["add", "task", "--due", "2020-01-01"], cwd=self.tmpdir)
        run_task_manager(["done", "1"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(
            ["list", "--overdue", "--today", "2025-06-01"], cwd=self.tmpdir
        )
        self.assertEqual(out, "")

    def test_overdue_without_today_defaults_to_real_date(self):
        """--overdue without --today uses real date"""
        # Use a date far in the past to ensure it's always overdue
        run_task_manager(["add", "task", "--due", "2020-01-01"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["list", "--overdue"], cwd=self.tmpdir)
        self.assertIn("task", out)

    def test_due_date_in_json_store(self):
        """Due date is stored correctly in tasks.json"""
        run_task_manager(["add", "task", "--due", "2025-12-25"], cwd=self.tmpdir)
        with open(os.path.join(self.tmpdir, "tasks.json"), "r") as f:
            data = json.load(f)
        self.assertEqual(data["tasks"]["1"]["due"], "2025-12-25")

    def test_suffix_order_priority_then_tags_then_due(self):
        """Suffix order: priority, then tags, then due date"""
        run_task_manager(
            ["add", "task", "--priority", "high", "--tag", "work", "--tag", "home", "--due", "2025-06-15"],
            cwd=self.tmpdir
        )
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(out, "1 [ ] task (high) #work #home due:2025-06-15")

    def test_no_due_task_has_no_suffix(self):
        """Tasks without --due show no due suffix"""
        run_task_manager(["add", "task"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(out, "1 [ ] task")

    def test_invalid_date_various_formats(self):
        """Various invalid date formats should all fail"""
        for bad_date in ["2026-13-01", "2026-00-01", "2026-01-32", "not-a-date", "2026/01/01"]:
            rc, out, err = run_task_manager(["add", "x", "--due", bad_date], cwd=self.tmpdir)
            self.assertEqual(rc, 1, f"Expected exit 1 for date {bad_date}")
            self.assertIn("Invalid date:", err, f"Expected 'Invalid date:' for date {bad_date}")


if __name__ == "__main__":
    unittest.main()
