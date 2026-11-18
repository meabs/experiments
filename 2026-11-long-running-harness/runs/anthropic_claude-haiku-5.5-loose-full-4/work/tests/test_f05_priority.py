import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestPriority(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_high_suffix(self):
        run(self.d, "add", "a", "--priority", "high")
        self.assertEqual(run(self.d, "list").stdout.splitlines(), ["1 [ ] a (high)"])

    def test_medium_no_suffix(self):
        run(self.d, "add", "a")
        self.assertEqual(run(self.d, "list").stdout.splitlines(), ["1 [ ] a"])

    def test_sort_by_priority(self):
        run(self.d, "add", "low1", "--priority", "low")
        run(self.d, "add", "med1")
        run(self.d, "add", "high1", "--priority", "high")
        run(self.d, "add", "med2")
        run(self.d, "add", "high2", "--priority", "high")
        r = run(self.d, "list", "--sort", "priority")
        self.assertEqual(r.stdout.splitlines(), [
            "3 [ ] high1 (high)", "5 [ ] high2 (high)",
            "2 [ ] med1", "4 [ ] med2", "1 [ ] low1 (low)"])

    def test_invalid_priority(self):
        r = run(self.d, "add", "a", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)


if __name__ == "__main__":
    unittest.main()
