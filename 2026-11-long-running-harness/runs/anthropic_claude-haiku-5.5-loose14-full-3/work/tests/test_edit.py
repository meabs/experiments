import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestEdit(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        run(self.dir, "add", "Buy milk")

    def test_edit_replaces_title(self):
        r = run(self.dir, "edit", "1", "--title", "New", "title")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "Edited 1\n")
        self.assertEqual(run(self.dir, "list").stdout, "1 [ ] New title\n")

    def test_unknown_id(self):
        r = run(self.dir, "edit", "9", "--title", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
