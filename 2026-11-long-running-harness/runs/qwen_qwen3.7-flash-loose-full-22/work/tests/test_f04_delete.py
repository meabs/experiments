"""Tests for feature F04: delete command."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


class TestF04Delete(unittest.TestCase):
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

    def test_delete_prints_deleted_id(self):
        self._run("add", "Buy milk")
        out, err, rc = self._run("delete", "1")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Deleted 1")

    def test_delete_removes_task(self):
        self._run("add", "Buy milk")
        self._run("delete", "1")
        out, err, rc = self._run("list")
        self.assertEqual(out, "No tasks")

    def test_next_add_gets_new_id_not_reused(self):
        self._run("add", "Buy milk")
        self._run("delete", "1")
        out, err, rc = self._run("add", "Walk dog")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 2")

    def test_unknown_id_exits_1(self):
        out, err, rc = self._run("delete", "9")
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", err)


if __name__ == "__main__":
    unittest.main()
