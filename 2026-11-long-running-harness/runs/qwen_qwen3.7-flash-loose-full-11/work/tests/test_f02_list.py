#!/usr/bin/env python3
"""Feature F02: list - lists tasks in id order, or 'No tasks'."""
import os, subprocess, sys, tempfile, unittest


class TestList(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_empty_list(self):
        stdout, _, rc = self.run_cmd("list")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_shows_tasks(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        stdout, _, _ = self.run_cmd("list")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")
