#!/usr/bin/env python3
"""Tests for feature F04: delete command."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestF04Delete(unittest.TestCase):
    """Test the 'delete' command."""

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

    def test_delete_prints_confirmation(self):
        """delete 2 prints 'Deleted 2'"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("delete", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 2")

    def test_next_add_gets_new_id_not_reused(self):
        """next add gets id 3, not 2"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "2")
        r = self._run("add", "New task")
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_unknown_id_exits_1(self):
        """unknown id -> 'No such task: <id>' exit 1"""
        self._run("add", "Buy milk")
        r = self._run("delete", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)

    def test_deleted_task_gone_from_list(self):
        """After delete, task is gone from list"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "2 [ ] Walk dog")

    def test_tasks_json_updated(self):
        """Verify tasks.json reflects deletion"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "1")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["id"], 2)
        self.assertEqual(data["next_id"], 3)


if __name__ == "__main__":
    unittest.main()
