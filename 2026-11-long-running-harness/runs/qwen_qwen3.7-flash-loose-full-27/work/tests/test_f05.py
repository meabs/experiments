#!/usr/bin/env python3
"""Tests for F05: priority feature."""

import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestPriority(unittest.TestCase):
    """F05: priority --priority high|medium|low, suffix display, sort, invalid error."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PY, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_add_high_priority_shows_suffix(self):
        """add a --priority high; list shows '1 [ ] a (high)'"""
        r = self._run("add", "a", "--priority", "high")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a (high)")

    def test_add_low_priority_shows_suffix(self):
        """add a --priority low; list shows '1 [ ] a (low)'"""
        r = self._run("add", "a", "--priority", "low")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a (low)")

    def test_add_medium_priority_no_suffix(self):
        """add a --priority medium; list shows '1 [ ] a' (no suffix)"""
        r = self._run("add", "a", "--priority", "medium")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a")

    def test_add_default_priority_is_medium(self):
        """add without --priority defaults to medium (no suffix)"""
        r = self._run("add", "a")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a")

    def test_list_sort_priority_orders_correctly(self):
        """list --sort priority orders high, medium, low, ties by id"""
        self._run("add", "Low task", "--priority", "low")
        self._run("add", "High task", "--priority", "high")
        self._run("add", "Med task", "--priority", "medium")
        r = self._run("list", "--sort", "priority")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("(high)", lines[0])
        self.assertNotIn("(high)", lines[1])
        self.assertNotIn("(low)", lines[1])
        self.assertIn("(low)", lines[2])

    def test_invalid_priority_error(self):
        """add --priority urgent exits 1 with 'Invalid priority: urgent'"""
        r = self._run("add", "a", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)

    def test_sort_priority_ties_by_id(self):
        """When priorities are equal, tasks are ordered by id"""
        self._run("add", "Second high", "--priority", "high")
        self._run("add", "First high", "--priority", "high")
        self._run("add", "Third high", "--priority", "high")
        r = self._run("list", "--sort", "priority")
        lines = r.stdout.strip().split("\n")
        # All high priority, should be in id order: 1, 2, 3
        self.assertEqual(lines[0], "1 [ ] Second high (high)")
        self.assertEqual(lines[1], "2 [ ] First high (high)")
        self.assertEqual(lines[2], "3 [ ] Third high (high)")


if __name__ == "__main__":
    unittest.main()
