#!/usr/bin/env python3
"""Tests for feature F01: add command."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest

# Find the absolute path to tasks.py (one level up from tests/)
TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


def run_tasks(*args, cwd=None):
    """Run tasks.py with given arguments and return (stdout, stderr, returncode)."""
    if cwd is None:
        cwd = os.getcwd()
    result = subprocess.run(
        ["python3", TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF01Add(unittest.TestCase):
    """Feature F01: add TITLE creates an open task and prints 'Added <id>'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_creates_task_prints_id(self):
        """Running: add 'Buy milk' -> Output is 'Added 1'."""
        stdout, stderr, rc = run_tasks("add", "Buy milk", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_second_add_gets_next_id(self):
        """Running another add; output is 'Added 2'."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("add", "Walk dog", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after adding a task."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_added_task_is_open(self):
        """The created task should be open (done=False)."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        task = data["tasks"][0]
        self.assertFalse(task["done"])
        self.assertEqual(task["title"], "Buy milk")
        self.assertEqual(task["id"], 1)


if __name__ == "__main__":
    unittest.main()
