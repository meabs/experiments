"""Tests for tasks.py - Feature F02: list command."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest


def run_tasks(cwd, args):
    """Run tasks.py with given args in a temp directory."""
    result = subprocess.run(
        ["python3", "tasks.py"] + args,
        cwd=cwd, capture_output=True, text=True
    )
    return result


class TestF02List(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy("tasks.py", self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_empty_list(self):
        """Empty list prints 'No tasks'."""
        r = run_tasks(self.tmpdir, ["list"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")
        self.assertEqual(r.stderr, "")

    def test_list_after_add(self):
        """After add, list shows the task."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        r = run_tasks(self.tmpdir, ["list"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "1 [ ] Buy milk")
        self.assertEqual(r.stderr, "")

    def test_list_multiple_tasks(self):
        """After multiple adds, list shows all tasks in id order."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        run_tasks(self.tmpdir, ["add", "Walk dog"])
        r = run_tasks(self.tmpdir, ["list"])
        self.assertEqual(r.returncode, 0)
        expected = "1 [ ] Buy milk\n2 [ ] Walk dog"
        self.assertEqual(r.stdout.strip(), expected)
        self.assertEqual(r.stderr, "")

    def test_list_shows_done_tasks(self):
        """List shows both open and done tasks."""
        run_tasks(self.tmpdir, ["add", "Task 1"])
        run_tasks(self.tmpdir, ["add", "Task 2"])
        run_tasks(self.tmpdir, ["done", "2"])
        r = run_tasks(self.tmpdir, ["list"])
        self.assertEqual(r.returncode, 0)
        expected = "1 [ ] Task 1\n2 [x] Task 2"
        self.assertEqual(r.stdout.strip(), expected)
        self.assertEqual(r.stderr, "")


if __name__ == "__main__":
    unittest.main()
