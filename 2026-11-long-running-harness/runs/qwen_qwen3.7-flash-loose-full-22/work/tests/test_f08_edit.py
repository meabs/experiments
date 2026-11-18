"""Tests for feature F08: edit command."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


class TestF08Edit(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        tf = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(tf):
            os.remove(tf)

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, TASKS_PY] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def test_edit_title_prints_edited(self):
        """edit 1 --title New title prints 'Edited 1'."""
        self._run("add", "old title")
        out, err, rc = self._run("edit", "1", "--title", "New", "title")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Edited 1")

    def test_edit_updates_list(self):
        """list shows the new title after editing."""
        self._run("add", "old title")
        self._run("edit", "1", "--title", "Updated title")
        out, _, _ = self._run("list")
        self.assertIn("Updated title", out)
        self.assertNotIn("old title", out)

    def test_edit_unknown_id_error(self):
        """unknown id -> 'No such task: <id>'."""
        self._run("add", "some task")
        out, err, rc = self._run("edit", "999", "--title", "New title")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 999", err)

    def test_edit_preserves_other_fields(self):
        """Editing title preserves priority, tags, due date."""
        self._run("add", "original", "--priority", "high", "--tag", "work", "--due", "2026-06-01")
        self._run("edit", "1", "--title", "changed")
        out, _, _ = self._run("list")
        self.assertIn("changed (high) #work due:2026-06-01", out)

    def test_edit_done_task(self):
        """Can edit a done task's title too."""
        self._run("add", "done task")
        self._run("done", "1")
        self._run("edit", "1", "--title", "still done but renamed")
        out, _, _ = self._run("list")
        self.assertIn("[x] still done but renamed", out)

    def test_edit_no_title_flag_error(self):
        """edit without --title flag is an error."""
        self._run("add", "task")
        out, err, rc = self._run("edit", "1")
        self.assertEqual(rc, 1)
        self.assertIn("--title", err)
