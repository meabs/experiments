#!/usr/bin/env python3
"""Feature F06: tags - --tag repeatable, suffix #tags, list --tag filter."""
import os, subprocess, sys, tempfile, unittest


class TestTags(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_tags_suffix_order(self):
        """F06: tag suffix comes after priority suffix"""
        self.run_cmd("add", "A", "--priority", "high", "--tag", "work")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] A (high) #work")

    def test_list_tag_filter(self):
        """F06: list --tag filters tasks with that tag"""
        self.run_cmd("add", "Work thing", "--tag", "work")
        self.run_cmd("add", "Home thing", "--tag", "home")
        self.run_cmd("add", "Both", "--tag", "work", "--tag", "home")
        stdout, _, _ = self.run_cmd("list", "--tag", "work")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        ids = [int(l.split()[0]) for l in lines]
        self.assertIn(1, ids)
        self.assertIn(3, ids)
