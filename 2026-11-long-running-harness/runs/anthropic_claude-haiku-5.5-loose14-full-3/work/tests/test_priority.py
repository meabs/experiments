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
        self.dir = tempfile.mkdtemp()

    def test_priority_suffix(self):
        run(self.dir, "add", "a", "--priority", "high")
        run(self.dir, "add", "b")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout, "1 [ ] a (high)\n2 [ ] b\n")

    def test_low_suffix(self):
        run(self.dir, "add", "a", "--priority", "low")
        self.assertEqual(run(self.dir, "list").stdout, "1 [ ] a (low)\n")

    def test_sort_by_priority(self):
        run(self.dir, "add", "low1", "--priority", "low")
        run(self.dir, "add", "med1")
        run(self.dir, "add", "high1", "--priority", "high")
        run(self.dir, "add", "med2", "--priority", "medium")
        run(self.dir, "add", "high2", "--priority", "high")
        r = run(self.dir, "list", "--sort", "priority")
        self.assertEqual(r.stdout.splitlines(), [
            "3 [ ] high1 (high)", "5 [ ] high2 (high)",
            "2 [ ] med1", "4 [ ] med2", "1 [ ] low1 (low)"])

    def test_invalid_priority(self):
        r = run(self.dir, "add", "a", "--priority", "urgent")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Invalid priority: urgent", r.stderr)


if __name__ == "__main__":
    unittest.main()
