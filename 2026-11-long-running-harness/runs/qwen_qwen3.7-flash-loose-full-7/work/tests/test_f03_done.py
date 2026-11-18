#!/usr/bin/env python3
"""Tests for feature F03: done command."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestF03Done(unittest.TestCase):
    """Test the 'done' command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        shutil.copy(os.path.join(self.orig_cwd, "tasks.py"), self.tmpdir)
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_done_prints_confirmation(self):
        """done 2 prints 'Done 2'"""
        self._run("add", "Buy milk")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_done_marks_task_done_in_list(self):
        """list shows '[x]' for done task"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        """done 9 exits 1 with 'No such task: 9'"""
        self._run("add", "Buy milk")
        r = self._run("done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)

    def test_done_invalid_id_exits_1(self):
        """done with non-numeric id exits 1"""
        self._run("add", "Buy milk")
        r = self._run("done", "abc")
        self.assertEqual(r.returncode, 1)

    def test_done_updates_json(self):
        """Verify tasks.json has done=true after done"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertTrue(data["tasks"][0]["done"])


if __name__ == "__main__":
    unittest.main()
