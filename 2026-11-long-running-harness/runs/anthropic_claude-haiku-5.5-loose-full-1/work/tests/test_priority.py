import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.py"))


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestPriority(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_suffix_and_default(self):
        run(self.dir, "add", "a", "--priority", "high")
        run(self.dir, "add", "b")
        run(self.dir, "add", "c", "--priority", "low")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a (high)", "2 [ ] b", "3 [ ] c (low)"])

    def test_sort_by_priority(self):
        run(self.dir, "add", "low1", "--priority", "low")
        run(self.dir, "add", "med1")
        run(self.dir, "add", "high1", "--priority", "high")
        run(self.dir, "add", "med2", "--priority", "medium")
        run(self.dir, "add", "high2", "--priority", "high")
        r = run(self.dir, "list", "--sort", "priority")
        self.assertEqual([l.split("] ", 1)[1] for l in r.stdout.splitlines()],
                         ["high1 (high)", "high2 (high)", "med1", "med2", "low1 (low)"])

    def test_invalid_priority(self):
        r = run(self.dir, "add", "x", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)


if __name__ == "__main__":
    unittest.main()
