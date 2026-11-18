"""Tests for tasks.py - Feature F03: done command."""

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


class TestF03Done(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy("tasks.py", self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_done_prints_message(self):
        """done 1 prints 'Done 1'."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        r = run_tasks(self.tmpdir, ["done", "1"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")
        self.assertEqual(r.stderr, "")

    def test_done_marks_task_done(self):
        """list shows the task as done after done command."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        run_tasks(self.tmpdir, ["done", "1"])
        r = run_tasks(self.tmpdir, ["list"])
        self.assertEqual(r.stdout.strip(), "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        """done on unknown id exits 1 with error message."""
        r = run_tasks(self.tmpdir, ["done", "99"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 99", r.stderr)

    def test_done_already_done_still_works(self):
        """Done on an already-done task still works (marks done again)."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        run_tasks(self.tmpdir, ["done", "1"])
        r = run_tasks(self.tmpdir, ["done", "1"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")


if __name__ == "__main__":
    unittest.main()
