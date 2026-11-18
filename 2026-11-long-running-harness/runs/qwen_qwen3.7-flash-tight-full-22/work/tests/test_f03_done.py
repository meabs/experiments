"""Test Feature 03: done command."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestF03Done(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy("tasks.py", self.tmpdir)
        self.tasks_file = os.path.join(self.tmpdir, "tasks.json")
        self.history_file = os.path.join(self.tmpdir, "history.json")

    def run_tasks(self, *args):
        result = subprocess.run(
            [sys.executable, "tasks.py"] + list(args),
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def tearDown(self):
        for f in ["tasks.json", "history.json"]:
            path = os.path.join(self.tmpdir, f)
            if os.path.exists(path):
                os.remove(path)
        try:
            os.rmdir(self.tmpdir)
        except OSError:
            pass

    def test_done_prints_message(self):
        self.run_tasks("add", "Buy milk")
        stdout, stderr, rc = self.run_tasks("done", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")

    def test_done_marks_task_done_in_list(self):
        self.run_tasks("add", "Buy milk")
        self.run_tasks("done", "1")
        stdout, _, _ = self.run_tasks("list")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        stdout, stderr, rc = self.run_tasks("done", "99")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "No such task: 99")

    def test_done_second_task(self):
        self.run_tasks("add", "Buy milk")
        self.run_tasks("add", "Walk dog")
        stdout, _, _ = self.run_tasks("done", "2")
        self.assertEqual(stdout, "Done 2")
        stdout, _, _ = self.run_tasks("list")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [x] Walk dog")


if __name__ == "__main__":
    unittest.main()
