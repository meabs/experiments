"""Tests for tasks.py - Feature F01: add"""

import json
import os
import subprocess
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_add_prints_added_id(self):
        r = self._run("add", "Buy milk")
        self.assertEqual(r.stdout.strip(), "Added 1")
        self.assertEqual(r.returncode, 0)

    def test_add_multiple_increments_ids(self):
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        self._run("add", "Test task")
        self.assertTrue(os.path.exists("tasks.json"))

    def test_add_with_priority_high(self):
        r = self._run("add", "Task a", "--priority", "high")
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_with_priority_medium(self):
        r = self._run("add", "Task a", "--priority", "medium")
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_with_priority_low(self):
        r = self._run("add", "Task a", "--priority", "low")
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_with_invalid_priority(self):
        r = self._run("add", "Task a", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)

    def test_add_with_tag(self):
        r = self._run("add", "Task a", "--tag", "work", "--tag", "home")
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_with_due(self):
        r = self._run("add", "Task a", "--due", "2025-12-25")
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_with_invalid_date(self):
        r = self._run("add", "Task a", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)


if __name__ == "__main__":
    unittest.main()
