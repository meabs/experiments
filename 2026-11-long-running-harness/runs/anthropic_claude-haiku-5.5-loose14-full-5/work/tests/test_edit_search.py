import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.py"))


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestEditSearch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        run(self.dir, "add", "Buy Milk")
        run(self.dir, "add", "milkshake")
        run(self.dir, "add", "Walk dog")

    def test_edit(self):
        r = run(self.dir, "edit", "1", "--title", "New", "title")
        self.assertEqual(r.stdout.strip(), "Edited 1")
        self.assertEqual(run(self.dir, "list").stdout.splitlines()[0], "1 [ ] New title")

    def test_edit_unknown(self):
        r = run(self.dir, "edit", "9", "--title", "x")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 9")

    def test_search(self):
        r = run(self.dir, "search", "milk")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] Buy Milk", "2 [ ] milkshake"])

    def test_search_none(self):
        self.assertEqual(run(self.dir, "search", "zzz").stdout.strip(), "No matches")


if __name__ == "__main__":
    unittest.main()
