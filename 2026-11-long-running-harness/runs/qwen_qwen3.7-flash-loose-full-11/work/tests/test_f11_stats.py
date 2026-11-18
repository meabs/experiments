#!/usr/bin/env python3
"""Feature F11: stats - prints open, done, total counts."""
import os, subprocess, sys, tempfile, unittest


class TestStats(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_stats_empty(self):
        """F11: fresh store prints zeros"""
        stdout, _, _ = self.run_cmd("stats")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "open: 0")
        self.assertEqual(lines[1], "done: 0")
        self.assertEqual(lines[2], "total: 0")

    def test_stats_counts(self):
        """F11: counts are correct after operations"""
        self.run_cmd("add", "A")
        self.run_cmd("add", "B")
        self.run_cmd("done", "1")
        self.run_cmd("delete", "2")
        stdout, _, _ = self.run_cmd("stats")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "open: 0")
        self.assertEqual(lines[1], "done: 1")
        self.assertEqual(lines[2], "total: 1")
