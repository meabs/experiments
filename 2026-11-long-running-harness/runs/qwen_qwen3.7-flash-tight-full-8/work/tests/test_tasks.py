#!/usr/bin/env python3
"""Tests for tasks.py command-line task manager."""

import json
import os
import subprocess
import tempfile
import unittest


class TaskManagerTest(unittest.TestCase):
    """Base test class that runs tasks.py in a temp directory."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.tmpdir, "tasks.json")

    def run_cmd(self, *args):
        """Run tasks.py with given args and return (stdout, stderr, returncode)."""
        result = subprocess.run(
            ["python3", os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    # ---- F01: add ----

    def test_f01_add_prints_added_id(self):
        stdout, stderr, rc = self.run_cmd("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_f01_add_multiple_ids(self):
        self.run_cmd("add", "Buy milk")
        stdout, stderr, rc = self.run_cmd("add", "Walk dog")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    def test_f01_data_file_created(self):
        self.run_cmd("add", "Buy milk")
        self.assertTrue(os.path.exists(self.data_file))

    # ---- F02: list ----

    def test_f02_empty_list(self):
        stdout, stderr, rc = self.run_cmd("list")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_f02_list_shows_tasks(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        stdout, stderr, rc = self.run_cmd("list")
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_f02_list_ordered_by_id(self):
        self.run_cmd("add", "Third")
        self.run_cmd("add", "First")
        self.run_cmd("add", "Second")
        stdout, _, _ = self.run_cmd("list")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "1 [ ] Third")
        self.assertEqual(lines[1], "2 [ ] First")
        self.assertEqual(lines[2], "3 [ ] Second")

    # ---- F03: done ----

    def test_f03_done_marks_task(self):
        self.run_cmd("add", "Buy milk")
        stdout, _, rc = self.run_cmd("done", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")

    def test_f03_done_reflected_in_list(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("done", "1")
        stdout, _, _ = self.run_cmd("list")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_f03_done_unknown_id_error(self):
        stdout, stderr, rc = self.run_cmd("done", "99")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)

    # ---- F04: delete ----

    def test_f04_delete_removes_task(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        self.run_cmd("delete", "1")
        stdout, _, rc = self.run_cmd("list")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "2 [ ] Walk dog")

    def test_f04_delete_prints_deleted(self):
        self.run_cmd("add", "Buy milk")
        stdout, _, rc = self.run_cmd("delete", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Deleted 1")

    def test_f04_ids_not_reused(self):
        self.run_cmd("add", "Task A")
        self.run_cmd("add", "Task B")
        self.run_cmd("delete", "1")
        stdout, _, rc = self.run_cmd("add", "Task C")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 3")

    def test_f04_delete_unknown_id_error(self):
        stdout, stderr, rc = self.run_cmd("delete", "99")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)

    # ---- F05: priority ----

    def test_f05_priority_high_suffix(self):
        self.run_cmd("add", "Urgent task", "--priority", "high")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] Urgent task (high)")

    def test_f05_priority_low_suffix(self):
        self.run_cmd("add", "Chill task", "--priority", "low")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] Chill task (low)")

    def test_f05_priority_medium_no_suffix(self):
        self.run_cmd("add", "Normal task", "--priority", "medium")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] Normal task")

    def test_f05_default_priority_medium(self):
        self.run_cmd("add", "Normal task")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] Normal task")

    def test_f05_invalid_priority_error(self):
        stdout, stderr, rc = self.run_cmd("add", "Bad", "--priority", "urgent")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid priority: urgent", stderr)

    def test_f05_sort_priority_order(self):
        self.run_cmd("add", "Low", "--priority", "low")
        self.run_cmd("add", "High", "--priority", "high")
        self.run_cmd("add", "Medium", "--priority", "medium")
        stdout, _, rc = self.run_cmd("list", "--sort", "priority")
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "2 [ ] High (high)")
        self.assertEqual(lines[1], "3 [ ] Medium")
        self.assertEqual(lines[2], "1 [ ] Low (low)")
