#!/usr/bin/env python3
"""Tests for tasks.py - command-line task manager."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


def run_task_manager(*args, cwd=None):
    """Run tasks.py and return (stdout, stderr, returncode)."""
    if cwd is None:
        cwd = os.getcwd()
    result = subprocess.run(
        ["python3", TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF01_Add(unittest.TestCase):
    """Feature 01: add - create tasks."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        path = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(path):
            os.remove(path)

    def _run(self, *args):
        return run_task_manager(*args, cwd=self.tmpdir)

    def test_add_creates_task_and_prints_id(self):
        stdout, stderr, rc = self._run("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_add_second_task_gets_id_2(self):
        self._run("add", "Buy milk")
        stdout, stderr, rc = self._run("add", "Walk dog")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    def test_tasks_json_exists_after_add(self):
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))


class TestF02_List(unittest.TestCase):
    """Feature 02: list - display tasks."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        path = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(path):
            os.remove(path)

    def _run(self, *args):
        return run_task_manager(*args, cwd=self.tmpdir)

    def test_empty_list(self):
        stdout, stderr, rc = self._run("list")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_shows_tasks_in_order(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        stdout, stderr, rc = self._run("list")
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


class TestF03_Done(unittest.TestCase):
    """Feature 03: done - mark tasks as done."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        path = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(path):
            os.remove(path)

    def _run(self, *args):
        return run_task_manager(*args, cwd=self.tmpdir)

    def test_done_marks_task(self):
        self._run("add", "Buy milk")
        stdout, stderr, rc = self._run("done", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")
        stdout2, _, _ = self._run("list")
        self.assertIn("[x] Buy milk", stdout2)

    def test_done_unknown_id(self):
        stdout, stderr, rc = self._run("done", "9")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "No such task: 9")


class TestF04_Delete(unittest.TestCase):
    """Feature 04: delete - remove tasks."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        path = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(path):
            os.remove(path)

    def _run(self, *args):
        return run_task_manager(*args, cwd=self.tmpdir)

    def test_delete_removes_task(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        stdout, _, rc = self._run("delete", "2")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Deleted 2")
        stdout2, _, _ = self._run("list")
        self.assertEqual(stdout2, "1 [ ] Buy milk")

    def test_delete_ids_not_reused(self):
        self._run("add", "Task 1")
        self._run("delete", "1")
        stdout, _, rc = self._run("add", "New task")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    def test_delete_unknown_id(self):
        stdout, stderr, rc = self._run("delete", "9")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "No such task: 9")


if __name__ == "__main__":
    unittest.main()
