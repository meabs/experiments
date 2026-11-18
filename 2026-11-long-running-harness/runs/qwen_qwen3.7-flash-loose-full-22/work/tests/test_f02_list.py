"""Tests for feature F02: list command."""

import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


class TestF02List(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, TASKS_PY] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def test_empty_list(self):
        out, err, rc = self._run("list")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "No tasks")

    def test_list_shows_tasks_in_id_order(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        out, err, rc = self._run("list")
        lines = out.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_after_done(self):
        self._run("add", "Buy milk")
        self._run("done", "1")
        out, err, rc = self._run("list")
        lines = out.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [x] Buy milk")


if __name__ == "__main__":
    unittest.main()
