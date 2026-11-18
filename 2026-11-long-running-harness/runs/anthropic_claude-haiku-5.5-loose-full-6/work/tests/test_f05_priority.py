import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd, capture_output=True, text=True)


class TestPriority(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_suffix(self):
        run(self.dir, "add", "a", "--priority", "high")
        run(self.dir, "add", "b", "--priority", "medium")
        run(self.dir, "add", "c", "--priority", "low")
        run(self.dir, "add", "d")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a (high)", "2 [ ] b", "3 [ ] c (low)", "4 [ ] d"])

    def test_sort_by_priority(self):
        run(self.dir, "add", "low1", "--priority", "low")
        run(self.dir, "add", "med1")
        run(self.dir, "add", "high1", "--priority", "high")
        run(self.dir, "add", "med2", "--priority", "medium")
        run(self.dir, "add", "high2", "--priority", "high")
        r = run(self.dir, "list", "--sort", "priority")
        self.assertEqual([l.split("] ", 1)[1].replace(" (high)", "").replace(" (low)", "") for l in r.stdout.splitlines()],
                         ["high1", "high2", "med1", "med2", "low1"])

    def test_invalid_priority(self):
        r = run(self.dir, "add", "x", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)
        self.assertEqual(run(self.dir, "list").stdout.strip(), "No tasks")


if __name__ == "__main__":
    unittest.main()
