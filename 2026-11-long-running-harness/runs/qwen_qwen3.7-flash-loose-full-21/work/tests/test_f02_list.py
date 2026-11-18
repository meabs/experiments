#!/usr/bin/env python3
"""Tests for tasks.py - Feature F02: list command."""

import json
import os
import subprocess
import tempfile
import unittest


class TestList(unittest.TestCase):
    """Test feature F02: list command."""

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

    def test_empty_list(self):
        """Empty list prints 'No tasks'."""
        r = self._run("list")
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_one_task(self):
        """One task shows correct format."""
        self._run("add", "Buy milk")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] Buy milk")

    def test_list_two_tasks(self):
        """Two tasks in id order."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


if __name__ == "__main__":
    unittest.main()
