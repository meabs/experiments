#!/usr/bin/env python3
"""Test feature: export --format json|csv"""
import subprocess
import os
import tempfile
import shutil
import unittest
import json


class TestF10Export(unittest.TestCase):
    """Test feature: export --format json|csv with the exact fields"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy(src, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_export_json_empty(self):
        """empty store exports []"""
        r = self._run("export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout.strip())
        self.assertEqual(data, [])

    def test_export_json_basic(self):
        """json: array of objects with id, title, done, priority, tags, due"""
        self._run("add", "Buy milk")
        r = self._run("export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout.strip())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["title"], "Buy milk")
        self.assertFalse(data[0]["done"])
        self.assertEqual(data[0]["priority"], "medium")
        self.assertEqual(data[0]["tags"], [])
        self.assertIsNone(data[0]["due"])

    def test_export_json_with_all_fields(self):
        """json includes all fields including priority, tags, due"""
        self._run("add", "Task one", "--priority", "high", "--tag", "work", "--due", "2026-12-31")
        self._run("done", "1")
        r = self._run("export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout.strip())
        self.assertEqual(data[0]["id"], 1)
        self.assertTrue(data[0]["done"])
        self.assertEqual(data[0]["priority"], "high")
        self.assertEqual(data[0]["tags"], ["work"])
        self.assertEqual(data[0]["due"], "2026-12-31")

    def test_export_csv_empty(self):
        """csv with no tasks has only header"""
        r = self._run("export", "--format", "csv")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertEqual(len(lines), 1)

    def test_export_csv_basic(self):
        """csv: header then rows, done as true/false, tags joined with ;"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("export", "--format", "csv")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertEqual(lines[1], "1,Buy milk,true,medium,,")

    def test_export_csv_with_tags_and_due(self):
        """csv tags joined with ;, due populated"""
        self._run("add", "Work task", "--tag", "urgent", "--tag", "review", "--due", "2025-06-15")
        r = self._run("export", "--format", "csv")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[1], "1,Work task,false,medium,urgent;review,2025-06-15")

    def test_export_in_id_order(self):
        """json and csv are sorted by id"""
        self._run("add", "Third task")
        self._run("add", "First task")
        self._run("add", "Second task")
        r = self._run("export", "--format", "json")
        data = json.loads(r.stdout.strip())
        ids = [t["id"] for t in data]
        self.assertEqual(ids, [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
