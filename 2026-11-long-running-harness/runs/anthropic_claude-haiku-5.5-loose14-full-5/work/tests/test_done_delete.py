import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.py"))


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestDoneDelete(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        run(self.dir, "add", "Buy milk")
        run(self.dir, "add", "Walk dog")

    def test_done(self):
        r = run(self.dir, "done", "2")
        self.assertEqual(r.stdout.strip(), "Done 2")
        self.assertIn("2 [x] Walk dog", run(self.dir, "list").stdout.splitlines())

    def test_done_unknown(self):
        r = run(self.dir, "done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 9")

    def test_delete_and_no_reuse(self):
        r = run(self.dir, "delete", "2")
        self.assertEqual(r.stdout.strip(), "Deleted 2")
        self.assertEqual(run(self.dir, "list").stdout.strip(), "1 [ ] Buy milk")
        self.assertEqual(run(self.dir, "add", "New").stdout.strip(), "Added 3")

    def test_delete_unknown(self):
        r = run(self.dir, "delete", "9")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 9")


if __name__ == "__main__":
    unittest.main()
