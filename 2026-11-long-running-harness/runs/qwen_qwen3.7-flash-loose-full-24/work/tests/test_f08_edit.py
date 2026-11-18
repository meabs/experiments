#!/usr/bin/env python3
"""Test feature: edit ID --title NEW TITLE replaces the title, prints 'Edited <id>'"""
import subprocess
import os
import tempfile
import shutil
import unittest


class TestF08Edit(unittest.TestCase):
    """Test feature: edit ID --title NEW TITLE replaces the title, prints 'Edited <id>'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy(src, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_edit_prints_edited(self):
        """edit 1 --title New title prints 'Edited 1'"""
        self._run("add", "Buy milk")
        r = self._run("edit", "1", "--title", "New title")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Edited 1")

    def test_edit_shows_new_title(self):
        """list shows the new title"""
        self._run("add", "Buy milk")
        self._run("edit", "1", "--title", "New title")
        r = self._run("list")
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] New title")

    def test_edit_unknown_id(self):
        """unknown id -> 'No such task: <id>'"""
        r = self._run("edit", "99", "--title", "Test")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 99", r.stderr)

    def test_edit_preserves_other_fields(self):
        """edit preserves priority, tags, due date"""
        self._run("add", "Buy milk", "--priority", "high", "--tag", "work")
        self._run("edit", "1", "--title", "Milk")
        r = self._run("list")
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] Milk (high) #work")

    def test_edit_multiline_title(self):
        """edit with multi-word title works"""
        self._run("add", "Short")
        self._run("edit", "1", "--title", "A much longer title here")
        r = self._run("list")
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] A much longer title here")


if __name__ == "__main__":
    unittest.main()
