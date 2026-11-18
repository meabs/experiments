#!/usr/bin/env python3
"""Tests for tasks.py - Feature F12: undo command."""

import json
import os
import subprocess
import tempfile
import unittest


class TestUndo(unittest.TestCase):
    """Test feature F12: undo command."""

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

    def test_undo_after_add(self):
        """undo after add removes it and next add reuses that id."""
        r = self._run("add", "Buy milk")
        self.assertEqual(r.stdout.strip(), "Added 1")
        
        r2 = self._run("undo")
        self.assertEqual(r2.stdout.strip(), "Undone")
        
        # Now add again - should get id 1 back
        r3 = self._run("add", "New task")
        self.assertEqual(r3.stdout.strip(), "Added 1")

    def test_undo_done(self):
        """undo reverts done back to open."""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        self.assertIn("[x]", r.stdout)
        
        self._run("undo")
        r2 = self._run("list")
        self.assertIn("[ ]", r2.stdout)

    def test_nothing_to_undo(self):
        """Nothing to undo exits 1."""
        r = self._run("undo")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Nothing to undo", r.stderr)

    def test_multiple_undo(self):
        """Multiple undos work in sequence."""
        self._run("add", "task1")
        self._run("add", "task2")
        self._run("add", "task3")
        
        self._run("undo")
        self._run("undo")
        self._run("undo")
        
        r = self._run("list")
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_undo_across_runs(self):
        """Undo history persists between runs."""
        self._run("add", "Buy milk")
        self._run("undo")
        # Run in a new process - undo history should persist
        r = self._run("list")
        self.assertEqual(r.stdout.strip(), "No tasks")


if __name__ == "__main__":
    unittest.main()
