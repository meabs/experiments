import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.py"))


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestTags(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_suffix_order(self):
        run(self.dir, "add", "a", "--tag", "work", "--tag", "home")
        run(self.dir, "add", "b", "--priority", "high", "--tag", "x")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a #work #home", "2 [ ] b (high) #x"])

    def test_filter(self):
        run(self.dir, "add", "a", "--tag", "work")
        run(self.dir, "add", "b", "--tag", "home")
        run(self.dir, "add", "c", "--tag", "work")
        r = run(self.dir, "list", "--tag", "work")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a #work", "3 [ ] c #work"])

    def test_filter_no_match(self):
        run(self.dir, "add", "a")
        r = run(self.dir, "list", "--tag", "work")
        self.assertEqual(r.stdout.splitlines(), ["No tasks"])


if __name__ == "__main__":
    unittest.main()
