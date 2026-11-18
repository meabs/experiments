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


class TestDone(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        run(self.dir, "add", "Buy milk")
        run(self.dir, "add", "Walk dog")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_done_prints_and_marks(self):
        r = run(self.dir, "done", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 2")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] Buy milk", "2 [x] Walk dog"])

    def test_done_unknown_id(self):
        r = run(self.dir, "done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 9")


if __name__ == "__main__":
    unittest.main()
