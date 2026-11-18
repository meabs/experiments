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


class TestDue(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_due_suffix_after_tags(self):
        run(self.dir, "add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a (low) #t due:2026-03-01"])

    def test_invalid_date(self):
        r = run(self.dir, "add", "a", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "tasks.json")))

    def test_overdue(self):
        run(self.dir, "add", "old", "--due", "2026-01-01")
        run(self.dir, "add", "future", "--due", "2026-12-01")
        run(self.dir, "add", "nodue")
        run(self.dir, "add", "done-old", "--due", "2025-01-01")
        run(self.dir, "done", "4")
        r = run(self.dir, "list", "--overdue", "--today", "2026-06-01")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] old due:2026-01-01"])

    def test_overdue_default_today_runs(self):
        run(self.dir, "add", "old", "--due", "2000-01-01")
        r = run(self.dir, "list", "--overdue")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] old due:2000-01-01"])


if __name__ == "__main__":
    unittest.main()
