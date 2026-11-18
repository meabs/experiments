#!/usr/bin/env python3
"""Tests for feature F04: delete command."""

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


class TestF04Delete(unittest.TestCase):
    """Feature F04: delete removes task, prints 'Deleted <id>'; ids never reused."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_delete_prints_task_id(self):
        """delete 1 prints 'Deleted 1'."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("delete", "1", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Deleted 1")

    def test_delete_removes_task_from_list(self):
        """After delete, list no longer shows the deleted task."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        run_tasks("delete", "1", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_next_add_reuses_no_deleted_id(self):
        """After deleting id 2, next add gets id 3, not 2."""
        run_tasks("add", "Task one", cwd=self.tmpdir)
        run_tasks("add", "Task two", cwd=self.tmpdir)
        run_tasks("add", "Task three", cwd=self.tmpdir)
        run_tasks("delete", "2", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("add", "New task", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 4")

    def test_delete_unknown_id_exits_1(self):
        """delete 99 exits 1 with 'No such task: 99' on stderr."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("delete", "99", cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)

    def test_delete_nonexistent_id_exits_1(self):
        """delete 1 when no tasks exist exits 1 with 'No such task: 1' on stderr."""
        stdout, stderr, rc = run_tasks("delete", "1", cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 1", stderr)


if __name__ == "__main__":
    unittest.main()
