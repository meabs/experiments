"""Tests for feature F02: list."""

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


class TestF02List(unittest.TestCase):
    """Feature F02: list prints one line per task in id order, or 'No tasks'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        setup_cwd(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_empty_list_prints_no_tasks(self):
        """Empty list prints 'No tasks'."""
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")
        self.assertEqual(stderr, "")

    def test_list_shows_tasks_in_id_order(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'."""
        run_tasks("add", "Buy milk", cwd=self.tmpdir)
        run_tasks("add", "Walk dog", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_single_task(self):
        """A single task shows correctly."""
        run_tasks("add", "Single task", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "1 [ ] Single task")

    def test_list_order_preserved_after_delete(self):
        """Tasks still listed in id order after deleting middle task."""
        run_tasks("add", "Task A", cwd=self.tmpdir)
        run_tasks("add", "Task B", cwd=self.tmpdir)
        run_tasks("add", "Task C", cwd=self.tmpdir)
        run_tasks("delete", "2", cwd=self.tmpdir)
        stdout, stderr, rc = run_tasks("list", cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Task A")
        self.assertEqual(lines[1], "3 [ ] Task C")


if __name__ == "__main__":
    unittest.main()
