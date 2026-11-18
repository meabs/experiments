#!/usr/bin/env python3
"""Tests for tasks.py - Feature F09: search command."""

import os
import subprocess
import tempfile
import unittest


class TestSearch(unittest.TestCase):
    """Test feature F09: search command."""

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

    def test_search_case_insensitive(self):
        """search matches case-insensitively."""
        self._run("add", "Buy Milk")
        r = self._run("search", "milk")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("Buy Milk", lines[0])

    def test_no_match(self):
        """No match prints 'No matches'."""
        self._run("add", "Buy milk")
        r = self._run("search", "xyz")
        self.assertEqual(r.stdout.strip(), "No matches")

    def test_search_multiline_title(self):
        """search works with multi-word titles."""
        self._run("add", "Buy milk and eggs")
        r = self._run("search", "milk and eggs")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("Buy milk and eggs", lines[0])


if __name__ == "__main__":
    unittest.main()
