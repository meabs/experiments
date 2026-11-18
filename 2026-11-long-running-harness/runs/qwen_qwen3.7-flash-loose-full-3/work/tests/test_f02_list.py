#!/usr/bin/env python3
"""Tests for feature F02: list command."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest

# Find the absolute path to tasks.py (one level up from tests/)
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


class TestF02List(unittest.TestCase):
    """Feature F02: list prints one line per task in id order, or 'No tasks'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_empty_list_prints_no_tasks(self):
        """Empty list prints 'No tasks'."""
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_shows_tasks_in_id_order(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        run_tasks("add", "Walk dog", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_after_done_shows_x(self):
        """Done tasks show [x] instead of [ ]."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        run_tasks("done", "1", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_list_after_delete_excludes_deleted(self):
        """Deleted tasks are not shown in list."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        run_tasks("add", "Walk dog", cwd=self.tmpdir)
        run_tasks("delete", "1", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "2 [ ] Walk dog")


if __name__ == "__main__":
    unittest.main()
