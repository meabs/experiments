#!/usr/bin/env python3
"""Tests for tasks.py - Feature F04: delete command."""

import os
import subprocess
import tempfile
import unittest


class TestDelete(unittest.TestCase):
    """Test feature F04: delete command."""

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

    def test_delete_prints(self):
        """delete 2 prints 'Deleted 2'."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("delete", "2")
        self.assertEqual(r.stdout.strip(), "Deleted 2")

    def test_next_id_not_reused(self):
        """Next add gets id 3, not 2."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "2")
        r = self._run("add", "New task")
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_unknown_id(self):
        """Unknown id exits 1 with error."""
        r = self._run("delete", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
