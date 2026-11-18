#!/usr/bin/env python3
"""Tests for feature F01: add command."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Test the 'add' command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        # Copy tasks.py to temp dir
        shutil.copy(os.path.join(self.orig_cwd, "tasks.py"), self.tmpdir)
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_creates_task_and_prints_id(self):
        """Run: add 'Buy milk', output is 'Added 1'"""
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_second_task_gets_id_2(self):
        """Run another add; output is 'Added 2'"""
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after add"""
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_tasks_json_content(self):
        """Verify tasks.json has correct content after add"""
        self._run("add", "Buy milk")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        task = data["tasks"][0]
        self.assertEqual(task["id"], 1)
        self.assertEqual(task["title"], "Buy milk")
        self.assertFalse(task["done"])
        self.assertEqual(task["priority"], "medium")
        self.assertEqual(task["tags"], [])
        self.assertIsNone(task["due"])
        self.assertEqual(data["next_id"], 2)

    def test_add_with_default_options(self):
        """add without --priority, --tag, or --due uses defaults"""
        self._run("add", "Simple task")
        with open("tasks.json") as f:
            data = json.load(f)
        task = data["tasks"][0]
        self.assertEqual(task["priority"], "medium")
        self.assertEqual(task["tags"], [])
        self.assertIsNone(task["due"])


if __name__ == "__main__":
    unittest.main()
