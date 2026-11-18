"""Tests for tasks.py - Feature F01: add command."""

import subprocess
import json
import os
import tempfile
import shutil
import unittest

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_task(args, cwd):
    """Run tasks.py with given args in the given directory."""
    # Copy tasks.py into the working directory
    shutil.copy2(SCRIPT_PATH, os.path.join(cwd, "tasks.py"))
    result = subprocess.run(
        ["python3", "tasks.py"] + args,
        cwd=cwd, capture_output=True, text=True
    )
    return result


class TestAddF01(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up tasks.json if it exists
        tj = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(tj):
            os.remove(tj)

    def test_add_creates_task_and_prints_id(self):
        r = run_task(["add", "Buy milk"], self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_second_task(self):
        run_task(["add", "Buy milk"], self.tmpdir)
        r = run_task(["add", "Walk dog"], self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        run_task(["add", "Buy milk"], self.tmpdir)
        tj = os.path.join(self.tmpdir, "tasks.json")
        self.assertTrue(os.path.exists(tj))

    def test_multiword_title(self):
        r = run_task(["add", "Buy milk and eggs"], self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")


if __name__ == "__main__":
    unittest.main()
