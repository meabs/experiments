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

    def test_suffix_and_sort(self):
        run(self.dir, "add", "a", "--priority", "low")
        run(self.dir, "add", "b")
        run(self.dir, "add", "c", "--priority", "high")
        lines = run(self.dir, "list").stdout.splitlines()
        self.assertEqual(lines, ["1 [ ] a (low)", "2 [ ] b", "3 [ ] c (high)"])
        lines = run(self.dir, "list", "--sort", "priority").stdout.splitlines()
        self.assertEqual(lines, ["3 [ ] c (high)", "2 [ ] b", "1 [ ] a (low)"])

    def test_invalid(self):
        r = run(self.dir, "add", "x", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "Invalid priority: urgent")


if __name__ == "__main__":
    unittest.main()
