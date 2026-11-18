#!/usr/bin/env python3
"""Tests for tasks.py - Feature F01: add command."""

import json
import os
import subprocess
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    """Test feature F01: add command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        # Clean up
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        project_root = os.path.dirname(os.path.dirname(__file__))
        result = subprocess.run(
            ["python3", os.path.join(project_root, "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_creates_task(self):
        """add 'Buy milk' prints 'Added 1'."""
        r = self._run("add", "Buy milk")
        self.assertEqual(r.stdout.strip(), "Added 1")
        self.assertEqual(r.returncode, 0)

    def test_add_second_task(self):
        """Second add gets id 2."""
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists after add."""
        self._run("add", "test")
        self.assertTrue(os.path.exists("tasks.json"))

    def test_tasks_json_content(self):
        """tasks.json has correct structure."""
        self._run("add", "test title")
        with open("tasks.json") as f:
            data = json.load(f)
        # JSON stores integer keys as strings
        self.assertIn("1", data["tasks"])
        task = data["tasks"]["1"]
        self.assertEqual(task["title"], "test title")
        self.assertFalse(task["done"])
        self.assertEqual(data["next_id"], 2)


if __name__ == "__main__":
    unittest.main()
