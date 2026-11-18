#!/usr/bin/env python3
"""Feature F05: priority - --priority high|medium|low, suffixes, sort."""
import os, subprocess, sys, tempfile, unittest


class TestPriority(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_priority_high_suffix(self):
        self.run_cmd("add", "A", "--priority", "high")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] A (high)")

    def test_priority_low_suffix(self):
        self.run_cmd("add", "B", "--priority", "low")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] B (low)")

    def test_priority_medium_no_suffix(self):
        self.run_cmd("add", "C")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] C")

    def test_sort_by_priority(self):
        self.run_cmd("add", "B", "--priority", "low")
        self.run_cmd("add", "A", "--priority", "high")
        self.run_cmd("add", "C")
        stdout, _, _ = self.run_cmd("list", "--sort", "priority")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "2 [ ] A (high)")
        self.assertEqual(lines[1], "3 [ ] C")
        self.assertEqual(lines[2], "1 [ ] B (low)")
