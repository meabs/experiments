"""Tests for feature F01: add command."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Remove any existing tasks.json
        tf = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(tf):
            os.remove(tf)

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, TASKS_PY] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def test_add_prints_added_id(self):
        out, err, rc = self._run("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 1")

    def test_add_second_task(self):
        self._run("add", "Buy milk")
        out, err, rc = self._run("add", "Walk dog")
        self.assertEqual(out, "Added 2")

    def test_tasks_json_exists(self):
        self._run("add", "Buy milk")
        tf = os.path.join(self.tmpdir, "tasks.json")
        self.assertTrue(os.path.exists(tf))
        with open(tf) as f:
            data = json.load(f)
        self.assertIn("1", data["tasks"])


if __name__ == "__main__":
    unittest.main()
