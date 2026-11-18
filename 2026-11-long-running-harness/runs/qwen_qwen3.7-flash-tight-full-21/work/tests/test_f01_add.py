#!/usr/bin/env python3
"""Tests for Feature F01: add - creates an open task and prints 'Added <id>'."""

import json
import os
import subprocess
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Feature F01: add TITLE creates an open task and prints 'Added <id>'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_json = os.path.join(self.tmpdir, "tasks.json")

    def run_cmd(self, *args):
        """Run tasks.py with the given arguments in the temp directory."""
        cmd = ["python3", os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args)
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_prints_added_id(self):
        """Running: add 'Buy milk' -> Output is 'Added 1'."""
        r = self.run_cmd("add", "Buy milk")
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_creates_tasks_json(self):
        """tasks.json exists in cwd after adding."""
        self.run_cmd("add", "Buy milk")
        self.assertTrue(os.path.exists(self.tasks_json))

    def test_add_second_task_gets_id_2(self):
        """Run another add; output is 'Added 2'."""
        self.run_cmd("add", "Buy milk")
        r = self.run_cmd("add", "Walk dog")
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_add_stores_open_task(self):
        """Task stored as done=False in tasks.json."""
        self.run_cmd("add", "Buy milk")
        with open(self.tasks_json) as f:
            data = json.load(f)
        task = data["tasks"][1]
        self.assertFalse(task["done"])
        self.assertEqual(task["title"], "Buy milk")

    def test_add_default_priority_medium(self):
        """Default priority should be medium."""
        self.run_cmd("add", "Buy milk")
        with open(self.tasks_json) as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][1]["priority"], "medium")

    def test_add_next_id_increments(self):
        """Next ID increments correctly."""
        self.run_cmd("add", "First")
        self.run_cmd("add", "Second")
        self.run_cmd("add", "Third")
        with open(self.tasks_json) as f:
            data = json.load(f)
        self.assertEqual(data["next_id"], 4)


if __name__ == "__main__":
    unittest.main()
