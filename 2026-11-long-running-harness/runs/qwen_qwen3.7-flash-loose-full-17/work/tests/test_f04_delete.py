"""Tests for tasks.py - Feature F04: delete command."""

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


class TestF04Delete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy("tasks.py", self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_delete_prints_message(self):
        """delete 1 prints 'Deleted 1'."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        r = run_tasks(self.tmpdir, ["delete", "1"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 1")
        self.assertEqual(r.stderr, "")

    def test_delete_removes_task(self):
        """After delete, list shows no tasks."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        run_tasks(self.tmpdir, ["delete", "1"])
        r = run_tasks(self.tmpdir, ["list"])
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_delete_next_id_not_reused(self):
        """After deleting id 2, next add gets id 3, not 2."""
        run_tasks(self.tmpdir, ["add", "Task 1"])
        run_tasks(self.tmpdir, ["add", "Task 2"])
        run_tasks(self.tmpdir, ["add", "Task 3"])
        run_tasks(self.tmpdir, ["delete", "2"])
        r = run_tasks(self.tmpdir, ["add", "New task"])
        self.assertEqual(r.stdout.strip(), "Added 4")

    def test_delete_unknown_id_exits_1(self):
        """delete on unknown id exits 1 with error message."""
        r = run_tasks(self.tmpdir, ["delete", "99"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 99", r.stderr)

    def test_delete_preserves_other_tasks(self):
        """Deleting one task preserves others."""
        run_tasks(self.tmpdir, ["add", "Task 1"])
        run_tasks(self.tmpdir, ["add", "Task 2"])
        run_tasks(self.tmpdir, ["add", "Task 3"])
        run_tasks(self.tmpdir, ["delete", "2"])
        r = run_tasks(self.tmpdir, ["list"])
        expected = "1 [ ] Task 1\n3 [ ] Task 3"
        self.assertEqual(r.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
