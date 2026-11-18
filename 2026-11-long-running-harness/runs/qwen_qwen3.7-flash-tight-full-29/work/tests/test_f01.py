"""Test feature F01: add command."""

import json
import os
import subprocess
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.task_file = os.path.join(self.tmpdir, "tasks.json")
        self.history_file = os.path.join(self.tmpdir, "tasks_history.json")

    def run_tasks(self, *args):
        """Run tasks.py with given args in the temp dir."""
        env = os.environ.copy()
        env["TASKS_DATA_FILE"] = self.task_file
        result = subprocess.run(
            ["python3", "/tmp/lrh-work/qwen_qwen3.7-flash-tight-full-29/tasks.py"] + list(args),
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
        )
        return result

    def test_add_creates_task_and_prints_id(self):
        """add 'Buy milk' should print 'Added 1'."""
        result = self.run_tasks("add", "Buy milk")
        self.assertEqual(result.stdout.strip(), "Added 1")
        self.assertEqual(result.returncode, 0)

    def test_add_second_task_gets_next_id(self):
        """Second add should get id 2."""
        self.run_tasks("add", "Buy milk")
        result = self.run_tasks("add", "Walk dog")
        self.assertEqual(result.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json should exist after add."""
        self.run_tasks("add", "Buy milk")
        self.assertTrue(os.path.exists(self.task_file))

    def test_added_task_is_open(self):
        """The added task should be open (done=False)."""
        self.run_tasks("add", "Buy milk")
        with open(self.task_file) as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        self.assertFalse(data["tasks"][0]["done"])
        self.assertEqual(data["tasks"][0]["title"], "Buy milk")
        self.assertEqual(data["next_id"], 2)


if __name__ == "__main__":
    unittest.main()
