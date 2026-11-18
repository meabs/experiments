import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        run(self.dir, "add", "Buy Milk")
        run(self.dir, "add", "milkshake")
        run(self.dir, "add", "Walk dog")

    def test_case_insensitive_substring(self):
        r = run(self.dir, "search", "milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "1 [ ] Buy Milk\n2 [ ] milkshake\n")

    def test_no_matches(self):
        r = run(self.dir, "search", "zzz")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "No matches\n")


if __name__ == "__main__":
    unittest.main()
