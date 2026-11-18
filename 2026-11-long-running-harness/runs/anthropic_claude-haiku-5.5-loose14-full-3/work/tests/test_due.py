import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestDue(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_suffix_after_tags(self):
        run(self.dir, "add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        self.assertEqual(run(self.dir, "list").stdout,
                         "1 [ ] a (low) #t due:2026-03-01\n")

    def test_invalid_date(self):
        r = run(self.dir, "add", "a", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)

    def test_overdue_open_only(self):
        run(self.dir, "add", "old", "--due", "2026-01-01")
        run(self.dir, "add", "old-done", "--due", "2026-01-02")
        run(self.dir, "add", "future", "--due", "2027-01-01")
        run(self.dir, "add", "nodue")
        run(self.dir, "done", "2")
        r = run(self.dir, "list", "--overdue", "--today", "2026-06-01")
        self.assertEqual(r.stdout, "1 [ ] old due:2026-01-01\n")

    def test_overdue_default_today_runs(self):
        run(self.dir, "add", "old", "--due", "2000-01-01")
        r = run(self.dir, "list", "--overdue")
        self.assertEqual(r.stdout, "1 [ ] old due:2000-01-01\n")

    def test_overdue_none(self):
        run(self.dir, "add", "x")
        self.assertEqual(run(self.dir, "list", "--overdue", "--today", "2026-01-01").stdout,
                         "No tasks\n")


if __name__ == "__main__":
    unittest.main()
