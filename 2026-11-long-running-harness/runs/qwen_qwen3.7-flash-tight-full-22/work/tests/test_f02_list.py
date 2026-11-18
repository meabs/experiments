"""Test Feature 02: list command."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestF02List(unittest.TestCase):
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

    def test_empty_list_prints_no_tasks(self):
        stdout, stderr, rc = self.run_tasks("list")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_after_add(self):
        self.run_tasks("add", "Buy milk")
        stdout, _, _ = self.run_tasks("list")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] Buy milk")

    def test_list_multiple_tasks_in_id_order(self):
        self.run_tasks("add", "Buy milk")
        self.run_tasks("add", "Walk dog")
        stdout, _, _ = self.run_tasks("list")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_shows_done_mark(self):
        self.run_tasks("add", "Buy milk")
        self.run_tasks("done", "1")
        stdout, _, _ = self.run_tasks("list")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [x] Buy milk")


if __name__ == "__main__":
    unittest.main()
