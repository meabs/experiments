#!/usr/bin/env python3
"""Tests for feature F06: tags."""

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


class TestF06Tags(unittest.TestCase):
    """Feature F06: --tag repeatable, suffix #work #home, list --tag work filters."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_single_tag_shows_suffix(self):
        """add a --tag work; list shows '1 [ ] a #work'."""
        stdout, stderr, rc = run_tasks("add", "a", "--tag", "work", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "1 [ ] a #work")

    def test_multiple_tags_show_in_order(self):
        """add a --tag work --tag home; list shows '1 [ ] a #work #home'."""
        stdout, stderr, rc = run_tasks("add", "a", "--tag", "work", "--tag", "home", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "1 [ ] a #work #home")

    def test_list_tag_filter_shows_matching(self):
        """list --tag work shows only tasks with that tag."""
        run_tasks("add", "a", "--tag", "work", cwd=self.tmpdir)
        run_tasks("add", "b", "--tag", "home", cwd=self.tmpdir)
        run_tasks("add", "c", "--tag", "work", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", "--tag", "work", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("#work", lines[0])
        self.assertIn("#work", lines[1])
        self.assertNotIn("#home", lines[0])
        self.assertNotIn("#home", lines[1])

    def test_list_tag_filter_excludes_non_matching(self):
        """list --tag work excludes tasks without the tag."""
        run_tasks("add", "a", "--tag", "work", cwd=self.tmpdir)
        run_tasks("add", "b", cwd=self.tmpdir)
        run_tasks("add", "c", "--tag", "home", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", "--tag", "work", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("#work", lines[0])

    def test_suffix_order_priority_then_tags(self):
        """suffix order: priority then tags."""
        stdout, stderr, rc = run_tasks("add", "a", "--priority", "high", "--tag", "work", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "1 [ ] a (high) #work")

    def test_no_tags_no_suffix(self):
        """add without --tag shows no tag suffix."""
        stdout, stderr, rc = run_tasks("add", "a", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "1 [ ] a")


if __name__ == "__main__":
    unittest.main()
