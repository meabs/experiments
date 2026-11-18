#!/usr/bin/env python3
"""Feature F07: due dates - --due YYYY-MM-DD, suffix, list --overdue."""
import os, subprocess, sys, tempfile, unittest


class TestDueDates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_due_suffix_in_line(self):
        """F07: due date appears as 'due:YYYY-MM-DD' after tags"""
        self.run_cmd("add", "A", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] A (low) #t due:2026-03-01")

    def test_list_overdue(self):
        """F07: list --overdue shows only open tasks due before --today"""
        self.run_cmd("add", "Past task", "--due", "2020-01-01")
        self.run_cmd("add", "Future task", "--due", "2099-12-31")
        stdout, _, _ = self.run_cmd("list", "--overdue", "--today", "2024-06-01")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("1 [ ] Past task", lines[0])
