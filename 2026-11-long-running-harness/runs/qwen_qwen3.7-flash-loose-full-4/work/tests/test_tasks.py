#!/usr/bin/env python3
"""Tests for tasks.py - Feature by feature."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_tasks(args, cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    result = subprocess.run(
        [sys.executable, TASKS_PY] + args,
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF01_Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_prints_id(self):
        stdout, _, rc = run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_add_second_task(self):
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        stdout, _, rc = run_tasks(["add", "Walk dog"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    def test_tasks_json_exists(self):
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))


class TestF02_List(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_list(self):
        stdout, _, rc = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_after_adds(self):
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["add", "Walk dog"], cwd=self.tmpdir)
        stdout, _, rc = run_tasks(["list"], cwd=self.tmpdir)
        lines = stdout.split(chr(10))
        self.assertEqual(len(lines), 2)
        self.assertIn("1 [ ] Buy milk", lines)
        self.assertIn("2 [ ] Walk dog", lines)


class TestF03_Done(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_done_marks_task(self):
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        stdout, _, rc = run_tasks(["done", "1"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")

    def test_done_shows_checkmark(self):
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["done", "1"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list"], cwd=self.tmpdir)
        self.assertIn("1 [x] Buy milk", stdout)

    def test_done_unknown_id(self):
        stdout, stderr, rc = run_tasks(["done", "99"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)


class TestF04_Delete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_delete_prints(self):
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        stdout, _, rc = run_tasks(["delete", "1"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Deleted 1")

    def test_delete_next_id_not_reused(self):
        run_tasks(["add", "Task 1"], cwd=self.tmpdir)
        run_tasks(["add", "Task 2"], cwd=self.tmpdir)
        run_tasks(["delete", "2"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["add", "New task"], cwd=self.tmpdir)
        self.assertEqual(stdout, "Added 3")

    def test_delete_unknown_id(self):
        stdout, stderr, rc = run_tasks(["delete", "99"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 99", stderr)


if __name__ == "__main__":
    unittest.main()


class TestF05_Priority(unittest.TestCase):
    """Feature 5: priority --priority high|medium|low, suffix '(high)'/'(low)', list --sort priority."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_high_priority(self):
        run_tasks(["add", "a", "--priority", "high"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list"], cwd=self.tmpdir)
        self.assertIn("1 [ ] a (high)", stdout)

    def test_add_low_priority(self):
        run_tasks(["add", "a", "--priority", "low"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list"], cwd=self.tmpdir)
        self.assertIn("1 [ ] a (low)", stdout)

    def test_add_medium_no_suffix(self):
        run_tasks(["add", "a", "--priority", "medium"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list"], cwd=self.tmpdir)
        self.assertNotIn("(high)", stdout)
        self.assertNotIn("(low)", stdout)

    def test_default_priority_is_medium(self):
        run_tasks(["add", "a"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list"], cwd=self.tmpdir)
        self.assertNotIn("(high)", stdout)
        self.assertNotIn("(low)", stdout)

    def test_sort_priority_orders_high_first(self):
        run_tasks(["add", "c", "--priority", "low"], cwd=self.tmpdir)
        run_tasks(["add", "b", "--priority", "high"], cwd=self.tmpdir)
        run_tasks(["add", "a", "--priority", "medium"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list", "--sort", "priority"], cwd=self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 3)
        # Order: high first, then medium, then low; ties by id
        # b(high)=2, a(medium)=3, c(low)=1
        self.assertIn("(high)", lines[0])
        self.assertIn("(low)", lines[2])
        # Line 1 is the medium task - no suffix, but it's in the middle
        self.assertIn("a", lines[1])

    def test_sort_priority_ties_by_id(self):
        run_tasks(["add", "c", "--priority", "high"], cwd=self.tmpdir)
        run_tasks(["add", "a", "--priority", "high"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list", "--sort", "priority"], cwd=self.tmpdir)
        lines = stdout.split("\n")
        # Both high priority, ordered by id: c(id=1) before a(id=2)
        self.assertIn("1 [ ] c (high)", lines[0])
        self.assertIn("2 [ ] a (high)", lines[1])

    def test_invalid_priority_error(self):
        _, stderr, rc = run_tasks(["add", "a", "--priority", "urgent"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("Invalid priority: urgent", stderr)


if __name__ == "__main__":
    unittest.main()


class TestF06_Tags(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_with_tags_shows_suffix(self):
        run_tasks(["add", "a", "--tag", "work", "--tag", "home"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list"], cwd=self.tmpdir)
        self.assertIn("1 [ ] a #work #home", stdout)

    def test_list_tag_filter(self):
        run_tasks(["add", "a", "--tag", "work"], cwd=self.tmpdir)
        run_tasks(["add", "b", "--tag", "home"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list", "--tag", "work"], cwd=self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("a", lines[0])
        self.assertNotIn("b", lines[0])

    def test_suffix_order_priority_then_tags(self):
        run_tasks(["add", "a", "--priority", "high", "--tag", "work"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list"], cwd=self.tmpdir)
        self.assertIn("(high) #work", stdout)
        # Make sure tags come after priority suffix
        self.assertIn("1 [ ] a (high) #work", stdout)


if __name__ == "__main__":
    unittest.main()


class TestF07_DueDates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        for f in ["tasks.json", ".undo_history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_with_due_shows_suffix(self):
        run_tasks(["add", "a", "--due", "2099-03-01"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list"], cwd=self.tmpdir)
        self.assertIn("due:2099-03-01", stdout)

    def test_invalid_date_error(self):
        _, stderr, rc = run_tasks(["add", "a", "--due", "2026-13-40"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2026-13-40", stderr)

    def test_overdue_filter_shows_only_open(self):
        # Add an overdue task and a non-overdue task
        run_tasks(["add", "old task", "--due", "2020-01-01"], cwd=self.tmpdir)
        run_tasks(["add", "future task", "--due", "2099-01-01"], cwd=self.tmpdir)
        # Mark the old task as done
        run_tasks(["done", "1"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list", "--overdue", "--today", "2025-01-01"], cwd=self.tmpdir)
        lines = stdout.split("\n")
        # Only the future task should NOT be shown (not overdue)
        # The old task is done so shouldn't show either
        self.assertNotIn("old task", "\n".join(lines))
        self.assertNotIn("future task", "\n".join(lines))

    def test_suffix_order_priority_tags_due(self):
        run_tasks(["add", "a", "--priority", "low", "--tag", "t", "--due", "2099-03-01"], cwd=self.tmpdir)
        stdout, _, _ = run_tasks(["list"], cwd=self.tmpdir)
        # Order should be: priority, tags, due
        self.assertIn("(low) #t due:2099-03-01", stdout)


if __name__ == "__main__":
    unittest.main()
