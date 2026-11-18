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

    def test_suffix_and_filter(self):
        run(self.dir, "add", "a", "--tag", "work", "--tag", "home")
        run(self.dir, "add", "b", "--priority", "high", "--tag", "home")
        run(self.dir, "add", "c")
        self.assertEqual(run(self.dir, "list").stdout.splitlines(),
                         ["1 [ ] a #work #home", "2 [ ] b (high) #home", "3 [ ] c"])
        self.assertEqual(run(self.dir, "list", "--tag", "work").stdout.splitlines(),
                         ["1 [ ] a #work #home"])


if __name__ == "__main__":
    unittest.main()
