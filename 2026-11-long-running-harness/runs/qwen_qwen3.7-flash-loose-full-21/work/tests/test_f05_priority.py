#!/usr/bin/env python3
"""Tests for tasks.py - Feature F05: priority."""

import os
import subprocess
import tempfile
import unittest


class TestPriority(unittest.TestCase):
    """Test feature F05: priority."""

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

    def test_add_with_priority_high(self):
        """add with --priority high shows suffix."""
        r = self._run("add", "a", "--priority", "high")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r2 = self._run("list")
        self.assertIn("(high)", r2.stdout)

    def test_add_with_priority_low(self):
        """add with --priority low shows suffix."""
        r = self._run("add", "a", "--priority", "low")
        self.assertIn("(low)", self._run("list").stdout)

    def test_medium_no_suffix(self):
        """Medium priority has no suffix."""
        self._run("add", "a")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        # Should not contain (high) or (low)
        self.assertNotIn("(high)", lines[0])
        self.assertNotIn("(low)", lines[0])

    def test_list_sort_priority(self):
        """list --sort priority orders high, medium, low, ties by id."""
        self._run("add", "c", "--priority", "low")
        self._run("add", "b", "--priority", "medium")
        self._run("add", "a", "--priority", "high")
        r = self._run("list", "--sort", "priority")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("(high)", lines[0])
        # Medium has no suffix per spec
        self.assertNotIn("(high)", lines[1])
        self.assertNotIn("(low)", lines[1])
        self.assertIn("(low)", lines[2])

    def test_invalid_priority(self):
        """Invalid priority value exits 1."""
        r = self._run("add", "a", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)


if __name__ == "__main__":
    unittest.main()
