"""Tests for tasks.py - Feature F01: add command."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Test the 'add' command (Feature F01)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.task_json = os.path.join(self.tmpdir, "tasks.json")
        # Copy tasks.py into the temp directory
        shutil.copy(os.path.join(os.path.dirname(__file__), '..', 'tasks.py'),
                    os.path.join(self.tmpdir, 'tasks.py'))

    def _run(self, *args):
        """Run tasks.py with given args in the temp directory."""
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_creates_task_and_prints_id(self):
        """add 'Buy milk' prints 'Added 1'."""
        result = self._run("add", "Buy milk")
        self.assertEqual(result.stdout.strip(), "Added 1")
        self.assertEqual(result.returncode, 0)

    def test_add_second_task_gets_id_2(self):
        """A second add gets id 2."""
        self._run("add", "Buy milk")
        result = self._run("add", "Walk dog")
        self.assertEqual(result.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """After adding, tasks.json exists in cwd."""
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(self.task_json))

    def test_tasks_json_valid(self):
        """tasks.json contains valid task data after add."""
        self._run("add", "Buy milk")
        with open(self.task_json) as f:
            data = json.load(f)
        # Task id 1 should exist in the tasks dict (key is string in JSON)
        self.assertIn("1", data["tasks"])
        self.assertEqual(data["tasks"]["1"]["title"], "Buy milk")
        self.assertFalse(data["tasks"]["1"]["done"])
        self.assertEqual(data["next_id"], 2)


if __name__ == "__main__":
    unittest.main()
