"""Tests for Feature F02: list - prints task lines in id order."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestF02List(unittest.TestCase):
    """Test the list command (F02)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_json = os.path.join(self.tmpdir, "tasks.json")
        script_path = os.path.join(os.path.dirname(__file__), "..", "tasks.py")
        shutil.copy2(script_path, self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            cwd=self.tmpdir,
            capture_output=True, text=True
        )
        return result

    def test_empty_list_prints_no_tasks(self):
        """Empty list prints 'No tasks'."""
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_shows_tasks_in_id_order(self):
        """After two adds, lines show tasks in id order."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_shows_done_status(self):
        """Done tasks show [x] instead of [ ]."""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")


if __name__ == "__main__":
    unittest.main()
