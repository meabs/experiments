import os
import shutil
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

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_high_suffix_and_medium_none(self):
        run(self.dir, "add", "a", "--priority", "high")
        run(self.dir, "add", "b")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a (high)", "2 [ ] b"])

    def test_low_suffix(self):
        run(self.dir, "add", "a", "--priority", "low")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a (low)"])

    def test_sort_by_priority_ties_by_id(self):
        run(self.dir, "add", "l1", "--priority", "low")
        run(self.dir, "add", "m1")
        run(self.dir, "add", "h1", "--priority", "high")
        run(self.dir, "add", "m2", "--priority", "medium")
        run(self.dir, "add", "h2", "--priority", "high")
        r = run(self.dir, "list", "--sort", "priority")
        self.assertEqual([l.split(" ", 3)[3].split(" (")[0] for l in r.stdout.splitlines()],
                         ["h1", "h2", "m1", "m2", "l1"])

    def test_invalid_priority(self):
        r = run(self.dir, "add", "a", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)
        self.assertEqual(run(self.dir, "list").stdout.strip(), "No tasks")


if __name__ == "__main__":
    unittest.main()
