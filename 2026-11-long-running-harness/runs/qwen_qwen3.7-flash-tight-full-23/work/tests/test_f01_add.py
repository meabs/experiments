"""Tests for Feature F01: add command."""
import json
import os
import subprocess
import tempfile
import unittest


class TestAddCommand(unittest.TestCase):
    """Test the add command (F01)."""

    def setUp(self):
        """Create a temporary directory for each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_file = os.path.join(self.tmpdir, "tasks.json")
        self.undo_file = os.path.join(self.tmpdir, ".undo.json")
        # Remove undo file to start clean
        if os.path.exists(self.undo_file):
            os.remove(self.undo_file)

    def run_tasks(self, *args):
        """Run tasks.py with given args in the temp directory."""
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_creates_task_and_prints_id(self):
        """add 'Buy milk' should print 'Added 1'."""
        result = self.run_tasks("add", "Buy milk")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")

    def test_add_second_task_gets_id_2(self):
        """Second add should print 'Added 2'."""
        self.run_tasks("add", "Buy milk")
        result = self.run_tasks("add", "Walk dog")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """After add, tasks.json must exist in cwd."""
        self.run_tasks("add", "Buy milk")
        self.assertTrue(os.path.exists(self.tasks_file))

    def test_tasks_json_content(self):
        """tasks.json should contain the correct task data."""
        self.run_tasks("add", "Buy milk")
        with open(self.tasks_file) as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        task = data["tasks"][0]
        self.assertEqual(task["id"], 1)
        self.assertEqual(task["title"], "Buy milk")
        self.assertFalse(task["done"])
        self.assertEqual(data["next_id"], 2)

    def test_add_with_priority_high(self):
        """add with --priority high."""
        result = self.run_tasks("add", "Urgent task", "--priority", "high")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")
        with open(self.tasks_file) as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["priority"], "high")

    def test_add_with_tags(self):
        """add with --tag."""
        result = self.run_tasks("add", "Work stuff", "--tag", "work", "--tag", "home")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")
        with open(self.tasks_file) as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["tags"], ["work", "home"])

    def test_add_with_due_date(self):
        """add with --due."""
        result = self.run_tasks("add", "Deadline task", "--due", "2026-03-01")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")
        with open(self.tasks_file) as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["due"], "2026-03-01")


if __name__ == "__main__":
    unittest.main()
