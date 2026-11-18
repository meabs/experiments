#!/usr/bin/env python3
"""Tests for feature F02: list command."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestF02List(unittest.TestCase):
    """Test the 'list' command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        shutil.copy(os.path.join(self.orig_cwd, "tasks.py"), self.tmpdir)
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_empty_list_prints_no_tasks(self):
        """Empty list prints 'No tasks'"""
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_after_one_add(self):
        """After one add, list shows '1 [ ] task title'"""
        self._run("add", "Buy milk")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "1 [ ] Buy milk")

    def test_list_after_two_adds(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_in_id_order(self):
        """Tasks listed in ascending id order regardless of add order"""
        # Add multiple tasks
        self._run("add", "Task C")
        self._run("add", "Task A")
        self._run("add", "Task B")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        ids = [int(line.split()[0]) for line in lines]
        self.assertEqual(ids, [1, 2, 3])

    def test_list_shows_done_marker(self):
        """Done tasks show [x] marker"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")


if __name__ == "__main__":
    unittest.main()
