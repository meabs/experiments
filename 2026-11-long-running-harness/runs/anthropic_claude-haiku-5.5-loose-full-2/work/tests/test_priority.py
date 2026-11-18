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
        run(self.dir, "add", "a", "--priority", "low")
        run(self.dir, "add", "b")
        run(self.dir, "add", "c", "--priority", "high")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a (low)", "2 [ ] b", "3 [ ] c (high)"])

    def test_sort_priority(self):
        run(self.dir, "add", "a", "--priority", "low")
        run(self.dir, "add", "b")
        run(self.dir, "add", "c", "--priority", "high")
        run(self.dir, "add", "d", "--priority", "high")
        r = run(self.dir, "list", "--sort", "priority")
        self.assertEqual(r.stdout.splitlines(),
                         ["3 [ ] c (high)", "4 [ ] d (high)", "2 [ ] b", "1 [ ] a (low)"])

    def test_invalid_priority(self):
        r = run(self.dir, "add", "a", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "tasks.json")))


if __name__ == "__main__":
    unittest.main()
