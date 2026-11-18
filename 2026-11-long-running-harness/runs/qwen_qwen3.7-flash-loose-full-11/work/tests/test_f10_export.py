#!/usr/bin/env python3
"""Feature F10: export - json and csv formats."""
import json, os, subprocess, sys, tempfile, unittest


class TestExport(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_export_json_empty(self):
        """F10: empty store exports [] in json"""
        stdout, _, _ = self.run_cmd("export", "--format", "json")
        data = json.loads(stdout)
        self.assertEqual(data, [])

    def test_export_json_with_tasks(self):
        """F10: json array of objects with correct keys"""
        self.run_cmd("add", "Task A", "--priority", "high", "--tag", "work", "--due", "2026-01-01")
        self.run_cmd("done", "1")
        stdout, _, _ = self.run_cmd("export", "--format", "json")
        data = json.loads(stdout)
        self.assertEqual(len(data), 1)
        t = data[0]
        self.assertEqual(t["id"], 1)
        self.assertEqual(t["title"], "Task A")
        self.assertTrue(t["done"])
        self.assertEqual(t["priority"], "high")
        self.assertEqual(t["tags"], ["work"])
        self.assertEqual(t["due"], "2026-01-01")

    def test_export_csv_header(self):
        """F10: csv has correct header"""
        self.run_cmd("add", "A")
        stdout, _, _ = self.run_cmd("export", "--format", "csv")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")

    def test_export_csv_done_as_true_false(self):
        """F10: done as true/false in csv"""
        self.run_cmd("add", "A")
        self.run_cmd("done", "1")
        stdout, _, _ = self.run_cmd("export", "--format", "csv")
        lines = stdout.split("\n")
        self.assertIn(",true,", lines[1])

    def test_export_csv_tags_joined_semicolon(self):
        """F10: tags joined with ; in csv"""
        self.run_cmd("add", "A", "--tag", "x", "--tag", "y")
        stdout, _, _ = self.run_cmd("export", "--format", "csv")
        lines = stdout.split("\n")
        self.assertIn("x;y", lines[1])
