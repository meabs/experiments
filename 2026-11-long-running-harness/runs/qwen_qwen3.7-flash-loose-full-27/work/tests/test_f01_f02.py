"""Tests for features F01 (add) and F02 (list)."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestAdd(unittest.TestCase):
    """F01: add TITLE creates an open task and prints 'Added <id>'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py into the test directory
        shutil.copy2(TASKS_PY, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_add_single_task(self):
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_multiple_tasks(self):
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_created(self):
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists("tasks.json"))

    def test_id_never_reused_after_delete(self):
        self._run("add", "Task 1")
        self._run("add", "Task 2")
        self._run("delete", "2")
        r = self._run("add", "Task 3")
        self.assertEqual(r.stdout.strip(), "Added 3")


class TestList(unittest.TestCase):
    """F02: list prints one line per task in id order, or 'No tasks'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PY, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_empty_list(self):
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_with_tasks(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_in_id_order(self):
        self._run("add", "Third")
        self._run("add", "First")
        self._run("add", "Second")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Third")
        self.assertEqual(lines[1], "2 [ ] First")
        self.assertEqual(lines[2], "3 [ ] Second")


if __name__ == "__main__":
    unittest.main()
