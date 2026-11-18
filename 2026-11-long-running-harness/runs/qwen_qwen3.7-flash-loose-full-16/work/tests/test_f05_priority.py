import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF05Priority(unittest.TestCase):
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

    def test_add_high_priority_shows_suffix(self):
        self._run("add", "Task a", "--priority", "high")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Task a (high)")

    def test_add_low_priority_shows_suffix(self):
        self._run("add", "Task b", "--priority", "low")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Task b (low)")

    def test_medium_no_suffix(self):
        self._run("add", "Task c", "--priority", "medium")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Task c")

    def test_default_is_medium(self):
        self._run("add", "Task d")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Task d")

    def test_sort_priority_orders_correctly(self):
        self._run("add", "Low task", "--priority", "low")
        self._run("add", "High task", "--priority", "high")
        self._run("add", "Med task", "--priority", "medium")
        result = self._run("list", "--sort", "priority")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("(high)", lines[0])
        self.assertNotIn("(high)", lines[1])
        self.assertIn("(low)", lines[2])

    def test_invalid_priority_exits_1(self):
        result = self._run("add", "Bad priority", "--priority", "urgent")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Invalid priority: urgent", result.stderr)


if __name__ == "__main__":
    unittest.main()
