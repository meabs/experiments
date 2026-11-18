#!/usr/bin/env python3
"""Feature F08: edit - replaces title, prints 'Edited <id>'."""
import os, subprocess, sys, tempfile, unittest


class TestEdit(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_edit_replaces_title(self):
        """F08: edit ID --title NEW TITLE replaces title"""
        self.run_cmd("add", "Old title")
        stdout, _, rc = self.run_cmd("edit", "1", "--title", "New Title")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Edited 1")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] New Title")

    def test_edit_unknown_id(self):
        """F08: unknown id -> 'No such task: <id>'"""
        stdout, stderr, rc = self.run_cmd("edit", "99", "--title", "New")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)
