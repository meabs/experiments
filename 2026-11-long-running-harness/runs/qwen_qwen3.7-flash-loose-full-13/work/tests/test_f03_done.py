"""Tests for tasks.py - Feature F03: done command."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestF03Done(unittest.TestCase):
    """Test the 'done' command (Feature F03)."""

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

    def test_done_prints_done_id(self):
        """done 1 prints 'Done 1'."""
        self._run("add", "Buy milk")
        result = self._run("done", "1")
        self.assertEqual(result.stdout.strip(), "Done 1")
        self.assertEqual(result.returncode, 0)

    def test_list_shows_done_marker(self):
        """After done, list shows [x] marker."""
        self._run("add", "Buy milk")
        self._run("done", "1")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        """done 99 exits 1 with 'No such task: 99'."""
        result = self._run("done", "99")
        self.assertIn("No such task: 99", result.stderr)
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
