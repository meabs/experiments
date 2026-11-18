#!/usr/bin/env python3
import unittest
import subprocess
import os
import tempfile
import json

class TestExport(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.taskfile = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            cwd=self.tmpdir, capture_output=True, text=True
        )
        return result

    def test_export_json_empty(self):
        """empty store exports []"""
        r = self._run("export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout.strip())
        self.assertEqual(data, [])

    def test_export_json_basic(self):
        """json: array of objects with id,title,done,priority,tags,due"""
        self._run("add", "Task one")
        r = self._run("export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout.strip())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["title"], "Task one")
        self.assertFalse(data[0]["done"])
        self.assertEqual(data[0]["priority"], "medium")
        self.assertEqual(data[0]["tags"], [])
        self.assertIsNone(data[0]["due"])

    def test_export_csv_empty(self):
        """csv empty exports header only"""
        r = self._run("export", "--format", "csv")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertEqual(len(lines), 1)

    def test_export_csv_basic(self):
        """csv: header then rows with done true/false, tags joined with ;"""
        self._run("add", "Task one")
        self._run("done", "1")
        r = self._run("export", "--format", "csv")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertIn("1,Task one,true,", lines[1])

    def test_export_csv_tags_joined_with_semicolon(self):
        """tags joined with ; in csv"""
        self._run("add", "Multi tag task", "--tag", "work", "--tag", "home")
        r = self._run("export", "--format", "csv")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        # Skip header
        self.assertIn("work;home", lines[1])


if __name__ == "__main__":
    unittest.main()
