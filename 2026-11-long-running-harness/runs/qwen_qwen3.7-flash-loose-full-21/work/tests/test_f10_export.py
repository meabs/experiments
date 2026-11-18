#!/usr/bin/env python3
"""Tests for tasks.py - Feature F10: export command."""

import json
import os
import subprocess
import tempfile
import unittest


class TestExport(unittest.TestCase):
    """Test feature F10: export command."""

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

    def test_export_json_empty(self):
        """Empty store exports [] in JSON."""
        r = self._run("export", "--format", "json")
        self.assertEqual(r.stdout.strip(), "[]")

    def test_export_json_content(self):
        """JSON export has correct fields."""
        self._run("add", "Buy milk", "--priority", "high", "--tag", "work", "--due", "2026-03-01")
        self._run("done", "1")
        r = self._run("export", "--format", "json")
        data = json.loads(r.stdout.strip())
        self.assertEqual(len(data), 1)
        task = data[0]
        self.assertEqual(task["id"], 1)
        self.assertEqual(task["title"], "Buy milk")
        self.assertTrue(task["done"])
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["tags"], ["work"])
        self.assertEqual(task["due"], "2026-03-01")

    def test_export_csv_header(self):
        """CSV export has correct header."""
        self._run("add", "test")
        r = self._run("export", "--format", "csv")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")

    def test_export_csv_content(self):
        """CSV export has correct content."""
        self._run("add", "test", "--tag", "a", "--tag", "b")
        r = self._run("export", "--format", "csv")
        lines = r.stdout.strip().split("\n")
        # Skip header
        row = lines[1].split(",")
        self.assertEqual(row[0], "1")
        self.assertEqual(row[1], "test")
        self.assertEqual(row[2], "false")
        self.assertEqual(row[4], "a;b")


if __name__ == "__main__":
    unittest.main()
