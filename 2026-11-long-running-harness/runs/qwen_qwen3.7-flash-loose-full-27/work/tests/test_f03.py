#!/usr/bin/env python3
"""Tests for F03: done command."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestDone(unittest.TestCase):
    """F03: done ID marks done, prints 'Done <id>'; unknown id -> stderr 'No such task: <id>', exit 1."""

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

    def test_done_marks_task_done(self):
        """done 2 prints 'Done 2'"""
        self._run("add", "Task 1")
        self._run("add", "Task 2")
        r = self._run("done", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 2")

    def test_list_shows_done_task(self):
        """list shows '2 [x] ...' after done"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("done", "2")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [x] Walk dog")

    def test_done_unknown_id(self):
        """done 9 exits 1 with 'No such task: 9'"""
        r = self._run("done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)

    def test_done_on_already_done(self):
        """done on an already-done task still works (marks done again)."""
        self._run("add", "Task 1")
        self._run("done", "1")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")
        # Verify it's still done
        r2 = self._run("list")
        self.assertIn("[x]", r2.stdout)

    def test_done_persists_across_runs(self):
        """done state persists across separate runs."""
        self._run("add", "Persistent task")
        self._run("done", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Persistent task")


if __name__ == "__main__":
    unittest.main()
