import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.py"))


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestDue(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_suffix(self):
        run(self.dir, "add", "a", "--tag", "t", "--due", "2026-03-01")
        self.assertEqual(run(self.dir, "list").stdout.strip(), "1 [ ] a #t due:2026-03-01")

    def test_invalid(self):
        r = run(self.dir, "add", "a", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "Invalid date: 2026-13-40")

    def test_overdue(self):
        run(self.dir, "add", "old", "--due", "2026-01-01")
        run(self.dir, "add", "future", "--due", "2027-01-01")
        run(self.dir, "add", "old done", "--due", "2026-01-02")
        run(self.dir, "done", "3")
        run(self.dir, "add", "nodue")
        r = run(self.dir, "list", "--overdue", "--today", "2026-06-01")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] old due:2026-01-01"])


if __name__ == "__main__":
    unittest.main()
