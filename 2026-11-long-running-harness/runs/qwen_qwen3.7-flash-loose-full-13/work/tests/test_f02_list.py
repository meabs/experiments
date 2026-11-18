"""Tests for tasks.py - Feature F02: list command."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestF02List(unittest.TestCase):
    """Test the 'list' command (Feature F02)."""

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

    def test_empty_list_prints_no_tasks(self):
        """Empty list prints 'No tasks'."""
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "No tasks")
        self.assertEqual(result.returncode, 0)

    def test_list_shows_single_task(self):
        """After one add, list shows the task."""
        self._run("add", "Buy milk")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] Buy milk")

    def test_list_shows_multiple_tasks_in_id_order(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_after_done_shows_done_marker(self):
        """Done tasks show [x] marker in list."""
        self._run("add", "Buy milk")
        self._run("done", "1")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")


if __name__ == "__main__":
    unittest.main()
