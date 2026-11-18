#!/usr/bin/env python3
"""Tests for feature F03: done command."""

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


class TestF03Done(unittest.TestCase):
    """Feature F03: done marks task done, prints 'Done <id>'; unknown id -> error."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_done_prints_task_id(self):
        """done 1 prints 'Done 1'."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("done", "1", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")

    def test_done_marks_task_as_done(self):
        """After done, list shows [x] for the task."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        run_tasks("done", "1", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        """done 99 exits 1 with 'No such task: 99' on stderr."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("done", "99", cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)

    def test_done_nonexistent_id_exits_1(self):
        """done 1 when no tasks exist exits 1 with 'No such task: 1' on stderr."""
        stdout, stderr, rc = run_tasks("done", "1", cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 1", stderr)

    def test_done_multiple_tasks_only_marks_target(self):
        """done 1 only marks task 1, not others."""
        run_tasks("add", "Task one", cwd=self.tmpdir)
        run_tasks("add", "Task two", cwd=self.tmpdir)
        run_tasks("done", "1", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [x] Task one")
        self.assertEqual(lines[1], "2 [ ] Task two")


if __name__ == "__main__":
    unittest.main()
