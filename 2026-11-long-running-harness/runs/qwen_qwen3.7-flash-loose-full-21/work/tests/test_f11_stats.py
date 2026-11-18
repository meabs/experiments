#!/usr/bin/env python3
"""Tests for tasks.py - Feature F11: stats command."""

import os
import subprocess
import tempfile
import unittest


class TestStats(unittest.TestCase):
    """Test feature F11: stats command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        project_root = os.path.dirname(os.path.dirname(__file__))
        result = subprocess.run(
            ["python3", os.path.join(project_root, "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_stats_empty(self):
        """Fresh store prints zeros."""
        r = self._run("stats")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "open: 0")
        self.assertEqual(lines[1], "done: 0")
        self.assertEqual(lines[2], "total: 0")

    def test_stats_counts(self):
        """Counts reflect current state."""
        self._run("add", "task1")
        self._run("add", "task2")
        self._run("done", "1")
        r = self._run("stats")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "open: 1")
        self.assertEqual(lines[1], "done: 1")
        self.assertEqual(lines[2], "total: 2")


if __name__ == "__main__":
    unittest.main()
