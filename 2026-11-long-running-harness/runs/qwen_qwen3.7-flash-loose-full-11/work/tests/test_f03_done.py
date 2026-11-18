#!/usr/bin/env python3
"""Feature F03: done - marks task done, prints 'Done <id>'."""
import os, subprocess, sys, tempfile, unittest


class TestDone(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_done_marks_task(self):
        self.run_cmd("add", "Buy milk")
        stdout, _, rc = self.run_cmd("done", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")
        # Verify with list
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [x] Buy milk")

    def test_done_unknown_id(self):
        stdout, stderr, rc = self.run_cmd("done", "99")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)
