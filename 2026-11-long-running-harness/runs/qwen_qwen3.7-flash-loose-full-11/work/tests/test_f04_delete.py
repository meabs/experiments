#!/usr/bin/env python3
"""Feature F04: delete - removes task, prints 'Deleted <id>', ids never reused."""
import os, subprocess, sys, tempfile, unittest


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_delete_removes_task(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        stdout, _, rc = self.run_cmd("delete", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Deleted 1")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "2 [ ] Walk dog")

    def test_delete_ids_never_reused(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("delete", "1")
        stdout, _, _ = self.run_cmd("add", "New task")
        self.assertEqual(stdout, "Added 2")

    def test_delete_unknown_id(self):
        stdout, stderr, rc = self.run_cmd("delete", "99")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)
