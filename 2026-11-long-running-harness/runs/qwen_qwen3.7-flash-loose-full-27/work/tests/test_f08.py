#!/usr/bin/env python3
"""Tests for F08: edit command."""

import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestEdit(unittest.TestCase):
    """F08: edit ID --title NEW TITLE replaces the title, prints 'Edited <id>'."""

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

    def test_edit_prints_edited_id(self):
        """edit 1 --title New title prints 'Edited 1'"""
        self._run("add", "Old title")
        r = self._run("edit", "1", "--title", "New title")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Edited 1")

    def test_edit_updates_title_in_list(self):
        """list shows the new title after edit"""
        self._run("add", "Old title")
        self._run("edit", "1", "--title", "New title")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] New title")

    def test_edit_unknown_id(self):
        """unknown id -> 'No such task: <id>'"""
        r = self._run("edit", "99", "--title", "Some title")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 99", r.stderr)

    def test_edit_with_multi_word_title(self):
        """edit preserves multi-word titles"""
        self._run("add", "Buy milk")
        self._run("edit", "1", "--title", "Buy eggs and cheese")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Buy eggs and cheese")

    def test_edit_persists_across_runs(self):
        """edit state persists across separate runs."""
        self._run("add", "Original")
        self._run("edit", "1", "--title", "Updated")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Updated")

    def test_edit_preserves_other_attributes(self):
        """edit only changes title, not done/priority/tags/due"""
        self._run("add", "Old title", "--priority", "high", "--tag", "work")
        self._run("done", "1")
        self._run("edit", "1", "--title", "New title")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] New title (high) #work")

    def test_edit_multiple_tasks(self):
        """editing one task doesn't affect others"""
        self._run("add", "Task A")
        self._run("add", "Task B")
        self._run("add", "Task C")
        self._run("edit", "2", "--title", "Modified B")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Task A")
        self.assertEqual(lines[1], "2 [ ] Modified B")
        self.assertEqual(lines[2], "3 [ ] Task C")


if __name__ == "__main__":
    unittest.main()
