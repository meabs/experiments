#!/usr/bin/env python3
"""Tests for F06: tags feature."""

import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestTags(unittest.TestCase):
    """F06: tags --tag repeatable, suffix '#work #home', list --tag work filters."""

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

    def test_add_with_tags_shows_suffix(self):
        """add a --tag work --tag home; list shows '1 [ ] a #work #home'"""
        r = self._run("add", "a", "--tag", "work", "--tag", "home")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a #work #home")

    def test_list_tag_filter_shows_only_matching(self):
        """list --tag work shows only tasks with that tag"""
        self._run("add", "task1", "--tag", "work")
        self._run("add", "task2", "--tag", "home")
        self._run("add", "task3", "--tag", "work")
        r = self._run("list", "--tag", "work")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("#work", lines[0])
        self.assertIn("#work", lines[1])
        self.assertNotIn("#home", "\n".join(lines))

    def test_suffix_order_priority_then_tags(self):
        """suffix order: priority then tags"""
        self._run("add", "a", "--priority", "low", "--tag", "t")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a (low) #t")

    def test_single_tag(self):
        """add with a single tag shows correctly"""
        r = self._run("add", "a", "--tag", "work")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a #work")

    def test_no_tags_no_suffix(self):
        """add without tags has no tag suffix"""
        r = self._run("add", "a")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a")

    def test_done_task_with_tags(self):
        """done task with tags still shows tags"""
        self._run("add", "a", "--tag", "work")
        self._run("done", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] a #work")

    def test_list_tag_filter_no_match(self):
        """list --tag with no matching tasks prints No tasks"""
        self._run("add", "a", "--tag", "work")
        r = self._run("list", "--tag", "home")
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_multiple_adds_different_tags(self):
        """multiple adds with different tags all persist correctly"""
        self._run("add", "first", "--tag", "alpha")
        self._run("add", "second", "--tag", "beta")
        self._run("add", "third", "--tag", "gamma")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("#alpha", lines[0])
        self.assertIn("#beta", lines[1])
        self.assertIn("#gamma", lines[2])


if __name__ == "__main__":
    unittest.main()
