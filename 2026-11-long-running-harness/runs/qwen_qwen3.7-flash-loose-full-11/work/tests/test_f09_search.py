#!/usr/bin/env python3
"""Feature F09: search - case-insensitive substring on title."""
import os, subprocess, sys, tempfile, unittest


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_search_case_insensitive(self):
        """F09: search matches case-insensitively"""
        self.run_cmd("add", "Buy Milk")
        self.run_cmd("add", "milkshake")
        stdout, _, _ = self.run_cmd("search", "milk")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)

    def test_search_no_matches(self):
        """F09: no match prints 'No matches'"""
        self.run_cmd("add", "Buy Milk")
        stdout, _, _ = self.run_cmd("search", "xyz")
        self.assertEqual(stdout, "No matches")
