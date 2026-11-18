#!/usr/bin/env python3
"""Tests for feature F05: priority."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


def run_tasks(*args, cwd=None):
    """Run tasks.py with given arguments and return (stdout, stderr, returncode)."""
    if cwd is None:
        cwd = os.getcwd()
    result = subprocess.run(
        ["python3", TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF05Priority(unittest.TestCase):
    """Feature F05: --priority high|medium|low, suffix (high)/(low), list --sort priority."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_high_priority_shows_suffix(self):
        """add a --priority high; list shows '1 [ ] a (high)'."""
        stdout, stderr, rc = run_tasks("add", "a", "--priority", "high", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "1 [ ] a (high)")

    def test_low_priority_shows_suffix(self):
        """add a --priority low; list shows '1 [ ] a (low)'."""
        stdout, stderr, rc = run_tasks("add", "a", "--priority", "low", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "1 [ ] a (low)")

    def test_medium_priority_no_suffix(self):
        """add a --priority medium; list shows '1 [ ] a' (no suffix)."""
        stdout, stderr, rc = run_tasks("add", "a", "--priority", "medium", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "1 [ ] a")

    def test_default_priority_is_medium(self):
        """add without --priority defaults to medium, no suffix."""
        stdout, stderr, rc = run_tasks("add", "a", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "1 [ ] a")

    def test_sort_priority_orders_correctly(self):
        """list --sort priority orders high, medium, low, ties by id."""
        # Add in reverse order so we can verify sorting
        run_tasks("add", "c", "--priority", "low", cwd=self.tmpdir)
        run_tasks("add", "b", "--priority", "high", cwd=self.tmpdir)
        run_tasks("add", "a", "--priority", "medium", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", "--sort", "priority", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 3)
        # First line should have (high)
        self.assertIn("(high)", lines[0])
        # Second line should NOT have (high) or (low) - it's medium
        self.assertNotIn("(high)", lines[1])
        self.assertNotIn("(low)", lines[1])
        # Third line should have (low)
        self.assertIn("(low)", lines[2])

    def test_invalid_priority_exits_1(self):
        """add --priority urgent exits 1 with 'Invalid priority: urgent'."""
        stdout, stderr, rc = run_tasks("add", "a", "--priority", "urgent", cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("Invalid priority: urgent", stderr)


if __name__ == "__main__":
    unittest.main()
