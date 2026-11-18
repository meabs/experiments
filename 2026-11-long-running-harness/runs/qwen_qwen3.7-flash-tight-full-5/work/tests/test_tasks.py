#!/usr/bin/env python3
"""Tests for tasks.py."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_PY = os.path.join(WORK_DIR, "tasks.py")


def run_task(args, cwd=None):
    """Run tasks.py with given args, return (stdout, stderr, returncode)."""
    if cwd is None:
        cwd = WORK_DIR
    result = subprocess.run(
        [sys.executable, "tasks.py"] + args,
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF01Add(unittest.TestCase):
    """Feature F01: add TITLE creates an open task and prints 'Added <id>'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PY, self.tmpdir)

    def tearDown(self):
        fpath = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(fpath):
            os.unlink(fpath)

    def test_add_first_task(self):
        """add 'Buy milk' outputs 'Added 1'."""
        stdout, stderr, rc = run_task(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertEqual(rc, 0, f"stderr: {stderr}")
        self.assertEqual(stdout, "Added 1")

    def test_add_second_task(self):
        """After one add, another add outputs 'Added 2'."""
        run_task(["add", "Buy milk"], cwd=self.tmpdir)
        stdout, stderr, rc = run_task(["add", "Walk dog"], cwd=self.tmpdir)
        self.assertEqual(rc, 0, f"stderr: {stderr}")
        self.assertEqual(stdout, "Added 2")

    def test_tasks_json_created(self):
        """tasks.json exists after add."""
        run_task(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))


class TestF02List(unittest.TestCase):
    """Feature F02: list prints one line per task in id order, or 'No tasks'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PY, self.tmpdir)

    def tearDown(self):
        fpath = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(fpath):
            os.unlink(fpath)

    def test_empty_list(self):
        """Empty list prints 'No tasks'."""
        stdout, stderr, rc = run_task(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0, f"stderr: {stderr}")
        self.assertEqual(stdout, "No tasks")

    def test_list_two_tasks(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'."""
        run_task(["add", "Buy milk"], cwd=self.tmpdir)
        run_task(["add", "Walk dog"], cwd=self.tmpdir)
        stdout, stderr, rc = run_task(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0, f"stderr: {stderr}")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_done_task_shows_x(self):
        """Done task shows [x] instead of [ ]."""
        run_task(["add", "Buy milk"], cwd=self.tmpdir)
        run_task(["done", "1"], cwd=self.tmpdir)
        stdout, stderr, rc = run_task(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0, f"stderr: {stderr}")
        self.assertEqual(stdout, "1 [x] Buy milk")

    def test_list_in_id_order(self):
        """Tasks are listed in id order regardless of add/delete order."""
        run_task(["add", "Task A"], cwd=self.tmpdir)
        run_task(["add", "Task B"], cwd=self.tmpdir)
        run_task(["add", "Task C"], cwd=self.tmpdir)
        run_task(["delete", "2"], cwd=self.tmpdir)
        stdout, stderr, rc = run_task(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0, f"stderr: {stderr}")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "1 [ ] Task A")
        self.assertEqual(lines[1], "3 [ ] Task C")


if __name__ == "__main__":
    unittest.main()
