#!/usr/bin/env python3
"""Tests for F04: delete command."""

import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestDelete(unittest.TestCase):
    """F04: delete ID removes the task, prints 'Deleted <id>'; ids are never reused."""

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

    def test_delete_prints_deleted_id(self):
        """delete 2 prints 'Deleted 2'"""
        self._run("add", "Task 1")
        self._run("add", "Task 2")
        r = self._run("delete", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 2")

    def test_delete_removes_task(self):
        """After delete, task is no longer in list"""
        self._run("add", "Task 1")
        self._run("add", "Task 2")
        self._run("delete", "2")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] Task 1")

    def test_next_add_reuses_no_id(self):
        """next add gets id 3, not 2"""
        self._run("add", "Task 1")
        self._run("add", "Task 2")
        self._run("delete", "2")
        r = self._run("add", "Task 3")
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_delete_unknown_id(self):
        """unknown id -> 'No such task: <id>' exit 1"""
        r = self._run("delete", "99")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 99", r.stderr)

    def test_delete_persists_across_runs(self):
        """delete state persists across separate runs."""
        self._run("add", "Persistent task")
        self._run("delete", "1")
        r = self._run("list")
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_delete_with_priority(self):
        """delete a task with priority - it's fully removed"""
        self._run("add", "High priority", "--priority", "high")
        self._run("add", "Low priority", "--priority", "low")
        self._run("delete", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "2 [ ] Low priority (low)")


if __name__ == "__main__":
    unittest.main()
