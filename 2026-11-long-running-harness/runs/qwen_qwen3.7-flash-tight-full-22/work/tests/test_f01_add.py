"""Test Feature 01: add command."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py into the temp directory
        shutil.copy("tasks.py", self.tmpdir)
        self.tasks_file = os.path.join(self.tmpdir, "tasks.json")
        self.history_file = os.path.join(self.tmpdir, "history.json")

    def run_tasks(self, *args):
        """Run tasks.py with given args and return (stdout, stderr, returncode)."""
        result = subprocess.run(
            [sys.executable, "tasks.py"] + list(args),
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def tearDown(self):
        # Clean up any files created in tmpdir
        for f in ["tasks.json", "history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)
        try:
            os.rmdir(self.tmpdir)
        except OSError:
            pass

    def test_add_creates_task_and_prints_id(self):
        stdout, stderr, rc = self.run_tasks("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_add_second_task_gets_next_id(self):
        self.run_tasks("add", "Buy milk")
        stdout, _, _ = self.run_tasks("add", "Walk dog")
        self.assertEqual(stdout, "Added 2")

    def test_tasks_json_exists_after_add(self):
        self.run_tasks("add", "Buy milk")
        self.assertTrue(os.path.exists(self.tasks_file))

    def test_tasks_json_content(self):
        self.run_tasks("add", "Buy milk")
        with open(self.tasks_file) as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        task = data["tasks"][0]
        self.assertEqual(task["id"], 1)
        self.assertEqual(task["title"], "Buy milk")
        self.assertFalse(task["done"])
        self.assertEqual(task["priority"], "medium")
        self.assertEqual(task["tags"], [])
        self.assertIsNone(task["due"])


if __name__ == "__main__":
    unittest.main()
