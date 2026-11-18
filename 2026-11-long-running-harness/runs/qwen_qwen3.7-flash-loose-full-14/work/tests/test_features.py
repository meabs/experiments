#!/usr/bin/env python3
"""Tests for tasks.py - Feature by feature."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_task(args, cwd=None):
    """Run tasks.py with given args and return (stdout, stderr, returncode)."""
    if cwd is None:
        # Use temp dir for isolation
        tmpdir = tempfile.mkdtemp()
        try:
            result = subprocess.run(
                [sys.executable, TASKS_PY] + args,
                capture_output=True, text=True, cwd=tmpdir
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode, tmpdir
        finally:
            pass  # Don't cleanup immediately so caller can inspect
    else:
        result = subprocess.run(
            [sys.executable, TASKS_PY] + args,
            capture_output=True, text=True, cwd=cwd
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode, None


class TestF01_Add(unittest.TestCase):
    """Feature 1: add command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_single_task(self):
        stdout, stderr, rc, _ = run_task(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_add_multiple_tasks(self):
        run_task(["add", "Buy milk"], cwd=self.tmpdir)
        stdout, _, rc, _ = run_task(["add", "Walk dog"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    def test_tasks_json_created(self):
        run_task(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))


class TestF02_List(unittest.TestCase):
    """Feature 2: list command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_empty_list(self):
        stdout, _, rc, _ = run_task(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_shows_tasks(self):
        run_task(["add", "Buy milk"], cwd=self.tmpdir)
        run_task(["add", "Walk dog"], cwd=self.tmpdir)
        stdout, _, rc, _ = run_task(["list"], cwd=self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


class TestF03_Done(unittest.TestCase):
    """Feature 3: done command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_done_marks_task(self):
        run_task(["add", "Buy milk"], cwd=self.tmpdir)
        stdout, _, rc, _ = run_task(["done", "1"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")
        stdout, _, _, _ = run_task(["list"], cwd=self.tmpdir)
        self.assertIn("1 [x] Buy milk", stdout)

    def test_done_unknown_id(self):
        stdout, stderr, rc, _ = run_task(["done", "99"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)


class TestF04_Delete(unittest.TestCase):
    """Feature 4: delete command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_delete_removes_task(self):
        run_task(["add", "Buy milk"], cwd=self.tmpdir)
        run_task(["add", "Walk dog"], cwd=self.tmpdir)
        stdout, _, rc, _ = run_task(["delete", "2"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Deleted 2")
        stdout, _, _, _ = run_task(["list"], cwd=self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Buy milk")

    def test_delete_next_id_not_reused(self):
        run_task(["add", "A"], cwd=self.tmpdir)
        run_task(["add", "B"], cwd=self.tmpdir)
        run_task(["delete", "2"], cwd=self.tmpdir)
        stdout, _, rc, _ = run_task(["add", "C"], cwd=self.tmpdir)
        self.assertEqual(stdout, "Added 3")

    def test_delete_unknown_id(self):
        stdout, stderr, rc, _ = run_task(["delete", "99"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)




class TestF05_Priority(unittest.TestCase):
    """Feature 5: priority command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_with_priority_high(self):
        stdout, _, rc, _ = run_task(["add", "urgent task", "--priority", "high"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")
        stdout, _, _, _ = run_task(["list"], cwd=self.tmpdir)
        self.assertIn("1 [ ] urgent task (high)", stdout)

    def test_add_with_priority_low(self):
        stdout, _, rc, _ = run_task(["add", "chill task", "--priority", "low"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")
        stdout, _, _, _ = run_task(["list"], cwd=self.tmpdir)
        self.assertIn("1 [ ] chill task (low)", stdout)

    def test_add_default_priority_medium_no_suffix(self):
        stdout, _, rc, _ = run_task(["add", "normal task"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        stdout, _, _, _ = run_task(["list"], cwd=self.tmpdir)
        self.assertIn("1 [ ] normal task", stdout)
        # medium should not have suffix
        self.assertNotIn("(medium)", stdout)

    def test_invalid_priority(self):
        stdout, stderr, rc, _ = run_task(["add", "task", "--priority", "urgent"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("Invalid priority: urgent", stderr)

    def test_list_sort_priority(self):
        run_task(["add", "low task", "--priority", "low"], cwd=self.tmpdir)
        run_task(["add", "high task", "--priority", "high"], cwd=self.tmpdir)
        run_task(["add", "med task", "--priority", "medium"], cwd=self.tmpdir)
        stdout, _, rc, _ = run_task(["list", "--sort", "priority"], cwd=self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("(high)", lines[0])
        self.assertIn("med task", lines[1])
        self.assertNotIn("(high)", lines[1])
        self.assertNotIn("(low)", lines[1])
        self.assertIn("(low)", lines[2])




class TestF07_DueDates(unittest.TestCase):
    """Feature 7: due dates command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_with_due_date(self):
        stdout, _, rc, _ = run_task(["add", "task a", "--due", "2026-03-01"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")
        stdout, _, _, _ = run_task(["list"], cwd=self.tmpdir)
        self.assertIn("1 [ ] task a due:2026-03-01", stdout)

    def test_invalid_date(self):
        stdout, stderr, rc, _ = run_task(["add", "task", "--due", "2026-13-40"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2026-13-40", stderr)

    def test_overdue_shows_open_tasks(self):
        # Add an overdue task (due before today)
        run_task(["add", "overdue task", "--due", "2020-01-01"], cwd=self.tmpdir)
        # Add a non-overdue task
        run_task(["add", "future task", "--due", "2030-01-01"], cwd=self.tmpdir)
        stdout, _, rc, _ = run_task(["list", "--overdue", "--today", "2025-01-01"], cwd=self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("overdue task", lines[0])
        self.assertNotIn("future task", lines[0])

    def test_suffix_order_priority_then_tags_then_due(self):
        stdout, _, rc, _ = run_task(["add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        stdout, _, _, _ = run_task(["list"], cwd=self.tmpdir)
        self.assertIn("1 [ ] a (low) #t due:2026-03-01", stdout)

    def test_done_tasks_not_in_overdue(self):
        run_task(["add", "done task", "--due", "2020-01-01"], cwd=self.tmpdir)
        run_task(["done", "1"], cwd=self.tmpdir)
        stdout, _, rc, _ = run_task(["list", "--overdue", "--today", "2025-01-01"], cwd=self.tmpdir)
        self.assertEqual(stdout, "No tasks")



class TestF08_Edit(unittest.TestCase):
    """Feature 8: edit command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_edit_replaces_title(self):
        run_task(["add", "Old title"], cwd=self.tmpdir)
        stdout, _, rc, _ = run_task(["edit", "1", "--title", "New title"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Edited 1")
        stdout, _, _, _ = run_task(["list"], cwd=self.tmpdir)
        self.assertIn("1 [ ] New title", stdout)

    def test_edit_unknown_id(self):
        stdout, stderr, rc, _ = run_task(["edit", "99", "--title", "New title"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)



if __name__ == "__main__":
    unittest.main()
