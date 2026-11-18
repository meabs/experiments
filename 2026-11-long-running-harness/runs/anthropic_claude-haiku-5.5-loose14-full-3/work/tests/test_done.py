import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestDone(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        run(self.dir, "add", "Buy milk")
        run(self.dir, "add", "Walk dog")

    def test_done_marks_task(self):
        r = run(self.dir, "done", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "Done 2\n")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout, "1 [ ] Buy milk\n2 [x] Walk dog\n")

    def test_unknown_id(self):
        r = run(self.dir, "done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
