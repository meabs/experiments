"""Tests for task manager."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_tasks(*args, cwd=None):
    """Run tasks.py with given args and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        [sys.executable, "tasks.py"] + list(args),
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def setup_cwd(cwd):
    """Copy tasks.py into the working directory and clean any existing data."""
    shutil.copy2(TASKS_PY, os.path.join(cwd, "tasks.py"))
    for f in ["tasks.json", "history.json"]:
        path = os.path.join(cwd, f)
        if os.path.exists(path):
            os.remove(path)


class TestF01Add(unittest.TestCase):
    """Feature F01: add TITLE creates an open task and prints 'Added <id>'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        setup_cwd(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_creates_task_and_prints_id(self):
        """add 'Buy milk' -> 'Added 1'"""
        stdout, stderr, rc = run_tasks("add", "Buy milk", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")
        self.assertEqual(stderr, "")

    def test_second_add_gets_id_2(self):
        """After another add, output is 'Added 2'."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("add", "Walk dog", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after add."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_tasks_json_contains_correct_data(self):
        """tasks.json contains the correct task data."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            tasks = json.load(f)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], 1)
        self.assertEqual(tasks[0]["title"], "Buy milk")
        self.assertFalse(tasks[0]["done"])


if __name__ == "__main__":
    unittest.main()
