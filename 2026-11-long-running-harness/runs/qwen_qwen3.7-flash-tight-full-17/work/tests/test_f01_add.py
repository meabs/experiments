#!/usr/bin/env python3
"""Tests for tasks.py - Feature F01: add command."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    """Test the add command (F01)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)

    def run_task(self, *args):
        """Run tasks.py with given arguments and return (stdout, stderr, returncode)."""
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def test_add_creates_task(self):
        """add creates a task and prints 'Added <id>'."""
        stdout, stderr, rc = self.run_task("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_add_multiple_tasks(self):
        """Multiple adds get incrementing IDs."""
        self.run_task("add", "Buy milk")
        stdout, _, _ = self.run_task("add", "Walk dog")
        self.assertEqual(stdout, "Added 2")

    def test_tasks_json_created(self):
        """Running add creates tasks.json."""
        self.run_task("add", "Buy milk")
        self.assertTrue(os.path.exists("tasks.json"))

    def test_tasks_json_content(self):
        """tasks.json contains correct data after add."""
        self.run_task("add", "Buy milk")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["title"], "Buy milk")
        self.assertFalse(data["tasks"][0]["done"])
        self.assertEqual(data["next_id"], 2)

    def test_add_title_with_spaces(self):
        """Title with spaces works correctly."""
        stdout, _, _ = self.run_task("add", "Buy milk and eggs")
        self.assertEqual(stdout, "Added 1")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["title"], "Buy milk and eggs")


if __name__ == "__main__":
    unittest.main()
