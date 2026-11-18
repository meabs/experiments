import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestStats(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_fresh_store_zeros(self):
        r = run(self.dir, "stats")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "open: 0\ndone: 0\ntotal: 0\n")

    def test_counts_exclude_deleted(self):
        run(self.dir, "add", "a")
        run(self.dir, "add", "b")
        run(self.dir, "add", "c")
        run(self.dir, "done", "1")
        run(self.dir, "delete", "2")
        r = run(self.dir, "stats")
        self.assertEqual(r.stdout, "open: 1\ndone: 1\ntotal: 2\n")


if __name__ == "__main__":
    unittest.main()
