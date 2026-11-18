"""Tests for feature F03: done command."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


class TestF03Done(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        tf = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(tf):
            os.remove(tf)

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, TASKS_PY] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def test_done_prints_done_id(self):
        self._run("add", "Buy milk")
        out, err, rc = self._run("done", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Done 1")

    def test_done_marks_task_as_done_in_list(self):
        self._run("add", "Buy milk")
        self._run("done", "1")
        out, err, rc = self._run("list")
        lines = out.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        out, err, rc = self._run("done", "9")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", err)

    def test_done_persists_to_json(self):
        self._run("add", "Buy milk")
        self._run("done", "1")
        tf = os.path.join(self.tmpdir, "tasks.json")
        with open(tf) as f:
            data = json.load(f)
        self.assertTrue(data["tasks"]["1"]["done"])


if __name__ == "__main__":
    unittest.main()
