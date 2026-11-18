#!/usr/bin/env python3
"""Tests for tasks.py - Feature F08: edit command."""

import os
import subprocess
import tempfile
import unittest


class TestEdit(unittest.TestCase):
    """Test feature F08: edit command."""

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

    def test_edit_prints(self):
        """edit 1 --title 'New title' prints 'Edited 1'."""
        self._run("add", "Buy milk")
        r = self._run("edit", "1", "--title", "New title")
        self.assertEqual(r.stdout.strip(), "Edited 1")

    def test_edit_updates_title(self):
        """list shows the new title."""
        self._run("add", "Buy milk")
        self._run("edit", "1", "--title", "New title")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] New title")

    def test_edit_unknown_id(self):
        """Unknown id exits 1 with error."""
        r = self._run("edit", "9", "--title", "New title")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
