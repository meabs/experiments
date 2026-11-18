"""Tests for Feature F01: add command."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    """Test cases for the 'add' command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py into the temp dir
        shutil.copy("tasks.py", self.tmpdir)
        self.tasks_json = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_creates_task_and_prints_id(self):
        """Run: add 'Buy milk'; Output is 'Added 1'"""
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_second_task_gets_id_2(self):
        """Run another add; output is 'Added 2'"""
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists_in_cwd(self):
        """tasks.json exists in cwd after add"""
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(self.tasks_json))

    def test_added_task_is_open(self):
        """After adding a task, list shows it as open [ ]"""
        self._run("add", "Buy milk")
        r = self._run("list")
        self.assertIn("[ ] Buy milk", r.stdout)

    def test_add_with_priority_high(self):
        """add with --priority high works"""
        r = self._run("add", "Urgent task", "--priority", "high")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_with_tags(self):
        """add with --tag works"""
        r = self._run("add", "Work task", "--tag", "work")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_with_multiple_tags(self):
        """add with multiple --tag flags works"""
        r = self._run("add", "Home work", "--tag", "work", "--tag", "home")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_with_due_date(self):
        """add with --due works"""
        r = self._run("add", "Due task", "--due", "2026-12-25")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_invalid_priority_exits_1(self):
        """add --priority invalid exits 1"""
        r = self._run("add", "Bad", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)

    def test_invalid_date_exits_1(self):
        """add --due invalid date exits 1"""
        r = self._run("add", "Bad", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)


if __name__ == "__main__":
    unittest.main()
