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

    def test_suffix_and_default(self):
        run(self.dir, "add", "a", "--priority", "high")
        run(self.dir, "add", "b")
        run(self.dir, "add", "c", "--priority", "low")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a (high)", "2 [ ] b", "3 [ ] c (low)"])

    def test_sort_priority(self):
        run(self.dir, "add", "low1", "--priority", "low")
        run(self.dir, "add", "med1")
        run(self.dir, "add", "high1", "--priority", "high")
        run(self.dir, "add", "med2", "--priority", "medium")
        run(self.dir, "add", "high2", "--priority", "high")
        r = run(self.dir, "list", "--sort", "priority")
        self.assertEqual(r.stdout.splitlines(), [
            "3 [ ] high1 (high)", "5 [ ] high2 (high)",
            "2 [ ] med1", "4 [ ] med2",
            "1 [ ] low1 (low)"])

    def test_invalid_priority(self):
        r = run(self.dir, "add", "a", "--priority", "urgent")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Invalid priority: urgent", r.stderr)
        self.assertEqual(run(self.dir, "list").stdout.strip(), "No tasks")


if __name__ == "__main__":
    unittest.main()
