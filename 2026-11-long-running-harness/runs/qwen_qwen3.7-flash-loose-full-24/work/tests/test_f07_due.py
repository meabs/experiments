#!/usr/bin/env python3
"""Test feature: due dates --due YYYY-MM-DD, suffix 'due:YYYY-MM-DD', invalid -> error, list --overdue"""
import subprocess
import os
import tempfile
import shutil
import unittest


class TestF07DueDates(unittest.TestCase):
    """Test feature: due dates"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy(src, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_with_due_shows_suffix(self):
        """add a --due 2026-03-01; list shows '1 [ ] a due:2026-03-01'"""
        r = self._run("add", "a", "--due", "2026-03-01")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] a due:2026-03-01")

    def test_invalid_date_error(self):
        """--due 2026-13-40 exits 1 with 'Invalid date: 2026-13-40'"""
        r = self._run("add", "a", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)

    def test_invalid_date_format_error(self):
        """--due bad-date exits 1 with 'Invalid date: bad-date'"""
        r = self._run("add", "a", "--due", "bad-date")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: bad-date", r.stderr)

    def test_overdue_filter(self):
        """--overdue shows only OPEN tasks due before --today"""
        # Add one overdue task (past due) and one future task
        self._run("add", "urgent", "--due", "2020-01-01")
        self._run("add", "later", "--due", "2099-12-31")
        # Mark urgent as done - should not show in overdue
        self._run("done", "1")
        r = self._run("list", "--overdue", "--today", "2025-06-15")
        lines = r.stdout.strip().split('\n')
        # Only the future-dated task ("later") is still open but NOT overdue
        # The urgent task IS overdue but is marked done
        # So we should see no overdue tasks
        self.assertEqual(lines, ["No tasks"])

    def test_overdue_shows_open_past_due(self):
        """Overdue filter correctly identifies open tasks past due date"""
        self._run("add", "past_due", "--due", "2020-01-01")
        self._run("add", "future_due", "--due", "2099-12-31")
        r = self._run("list", "--overdue", "--today", "2025-06-15")
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertIn("past_due", lines[0])
        self.assertNotIn("future_due", lines[0])

    def test_suffix_order_priority_tags_due(self):
        """suffix order: priority then tags then due"""
        r = self._run("add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        self.assertEqual(r.returncode, 0)
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] a (low) #t due:2026-03-01")

    def test_no_due_no_suffix(self):
        """task without due has no due suffix"""
        r = self._run("add", "a")
        self.assertEqual(r.returncode, 0)
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertNotIn("due:", lines[0])


if __name__ == "__main__":
    unittest.main()
