import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF07DueDates(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, os.path.join(self.dir, "tasks.py"))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            cwd=self.dir,
            capture_output=True, text=True
        )
        return result

    def test_add_with_due_shows_suffix(self):
        self._run("add", "Task x", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Task x (low) #t due:2026-03-01")

    def test_invalid_date_exits_1(self):
        result = self._run("add", "Bad date", "--due", "2026-13-40")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", result.stderr)

    def test_overdue_shows_open_tasks_before_today(self):
        self._run("add", "Overdue task", "--due", "2026-03-01")
        result = self._run("list", "--overdue", "--today", "2026-03-02")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("due:2026-03-01", lines[0])

    def test_not_overdue_when_due_equals_today(self):
        self._run("add", "Today task", "--due", "2026-03-01")
        result = self._run("list", "--overdue", "--today", "2026-03-01")
        self.assertEqual(result.stdout.strip(), "No tasks")


if __name__ == "__main__":
    unittest.main()
