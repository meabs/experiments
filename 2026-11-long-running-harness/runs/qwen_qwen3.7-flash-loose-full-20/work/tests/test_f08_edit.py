#!/usr/bin/env python3
import unittest
import subprocess
import os
import json
import tempfile

class TestEdit(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.taskfile = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            cwd=self.tmpdir, capture_output=True, text=True
        )
        return result

    def test_edit_replaces_title(self):
        """edit 1 --title New title prints 'Edited 1'"""
        # Add a task first
        r = self._run("add", "Old title")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Added 1", r.stdout)
        # Edit the task
        r = self._run("edit", "1", "--title", "New title")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Edited 1", r.stdout)
        # Verify via list
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertIn("New title", r.stdout)
        self.assertNotIn("Old title", r.stdout)

    def test_edit_shows_new_title_in_list(self):
        """list shows the new title"""
        self._run("add", "Original")
        self._run("edit", "1", "--title", "Updated title here")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Updated title here", r.stdout)

    def test_edit_unknown_id_exits_1(self):
        """unknown id -> 'No such task: <id>'"""
        r = self._run("edit", "99", "--title", "Something")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 99", r.stderr)

    def test_edit_undo_works(self):
        """undo reverts edit back to old title"""
        self._run("add", "Original")
        self._run("edit", "1", "--title", "Changed")
        r = self._run("undo")
        self.assertEqual(r.returncode, 0)
        r = self._run("list")
        self.assertIn("Original", r.stdout)


if __name__ == "__main__":
    unittest.main()
