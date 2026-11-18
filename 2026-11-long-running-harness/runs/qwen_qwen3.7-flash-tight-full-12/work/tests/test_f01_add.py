#!/usr/bin/env python3
"""Test feature F01: add command."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        # Copy tasks.py into the temp dir
        shutil.copy(os.path.join(self.old_cwd, "tasks.py"), self.tmpdir)
        # Clean up any existing files
        for f in ["tasks.json", ".tasks_history.json"]:
            if os.path.exists(f):
                os.remove(f)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        """Run tasks.py with given args, return (returncode, stdout, stderr)."""
        result = subprocess.run(
            [sys.executable, "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    def test_add_creates_task_with_id_1(self):
        """add TITLE creates task with id 1."""
        rc, out, err = self._run("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 1")
        # Check the data file
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["id"], 1)
        self.assertEqual(data["tasks"][0]["title"], "Buy milk")
        self.assertFalse(data["tasks"][0]["done"])

    def test_add_multiple_tasks_increment_ids(self):
        """Adding multiple tasks increments IDs."""
        self._run("add", "Task one")
        rc2, out2, _ = self._run("add", "Task two")
        self.assertEqual(out2, "Added 2")
        rc3, out3, _ = self._run("add", "Task three")
        self.assertEqual(out3, "Added 3")

    def test_add_title_with_spaces(self):
        """add handles multi-word titles."""
        rc, out, _ = self._run("add", "Buy groceries today")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 1")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["title"], "Buy groceries today")

    def test_add_default_priority_medium(self):
        """New tasks default to medium priority."""
        self._run("add", "Test")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["priority"], "medium")

    def test_add_default_empty_tags(self):
        """New tasks have empty tags by default."""
        self._run("add", "Test")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["tags"], [])

    def test_add_default_null_due(self):
        """New tasks have null due by default."""
        self._run("add", "Test")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertIsNone(data["tasks"][0]["due"])


if __name__ == "__main__":
    unittest.main()
