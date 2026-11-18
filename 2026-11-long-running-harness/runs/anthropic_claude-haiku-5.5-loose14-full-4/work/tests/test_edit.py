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


class TestEdit(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        run(self.dir, "add", "Buy milk")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_edit_replaces_title(self):
        r = run(self.dir, "edit", "1", "--title", "New", "title")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Edited 1")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] New title"])

    def test_edit_unknown_id(self):
        r = run(self.dir, "edit", "9", "--title", "x")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 9")


if __name__ == "__main__":
    unittest.main()
