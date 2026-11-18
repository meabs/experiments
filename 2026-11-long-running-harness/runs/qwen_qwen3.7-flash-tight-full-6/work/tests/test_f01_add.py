#!/usr/bin/env python3
import json
import os
import subprocess
import shutil
import tempfile
import unittest

# Path to tasks.py relative to this file's directory
TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


class TestF01Add(unittest.TestCase):
    """Feature F01: add TITLE creates an open task and prints 'Added <id>'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        # Copy tasks.py into the temp dir so it can be found
        shutil.copy2(TASKS_PY, os.path.join(self.tmpdir, "tasks.py"))

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_prints_added_id(self):
        """Run: add 'Buy milk' -> Output is 'Added 1'"""
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_second_task(self):
        """Run another add; output is 'Added 2'"""
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after adding"""
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_tasks_json_content(self):
        """Check the JSON content of tasks.json"""
        self._run("add", "Buy milk")
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        task = data["tasks"][0]
        self.assertEqual(task["id"], 1)
        self.assertEqual(task["title"], "Buy milk")
        self.assertFalse(task["done"])


if __name__ == "__main__":
    unittest.main()
