"""Tests for tasks.py - Feature F04: delete command."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestF04Delete(unittest.TestCase):
    """Test the 'delete' command (Feature F04)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.task_json = os.path.join(self.tmpdir, "tasks.json")
        shutil.copy(os.path.join(os.path.dirname(__file__), '..', 'tasks.py'),
                    os.path.join(self.tmpdir, 'tasks.py'))

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_delete_prints_deleted_id(self):
        """delete 1 prints 'Deleted 1'."""
        self._run("add", "Buy milk")
        result = self._run("delete", "1")
        self.assertEqual(result.stdout.strip(), "Deleted 1")
        self.assertEqual(result.returncode, 0)

    def test_next_add_reuses_no_id(self):
        """After delete 2, next add gets id 3, not 2."""
        self._run("add", "Task A")
        self._run("add", "Task B")
        self._run("add", "Task C")
        self._run("delete", "2")
        result = self._run("add", "Task D")
        self.assertEqual(result.stdout.strip(), "Added 4")

    def test_unknown_id_exits_1(self):
        """delete 99 exits 1 with 'No such task: 99'."""
        result = self._run("delete", "99")
        self.assertIn("No such task: 99", result.stderr)
        self.assertEqual(result.returncode, 1)

    def test_deleted_task_not_in_list(self):
        """After deleting, the task is no longer shown in list."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "1")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "2 [ ] Walk dog")

    def test_delete_removes_from_tasks_json(self):
        """After deleting, the task is removed from tasks.json."""
        self._run("add", "Buy milk")
        self._run("delete", "1")
        with open(self.task_json) as f:
            data = json.load(f)
        self.assertNotIn("1", data["tasks"])


if __name__ == "__main__":
    unittest.main()
