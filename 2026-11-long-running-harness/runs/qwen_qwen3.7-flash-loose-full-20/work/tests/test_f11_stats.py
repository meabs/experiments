#!/usr/bin/env python3
import unittest
import subprocess
import os
import tempfile

class TestStats(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.taskfile = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            cwd=self.tmpdir, capture_output=True, text=True
        )
        return result

    def test_stats_fresh_store(self):
        """fresh store prints zeros"""
        r = self._run("stats")
        self.assertEqual(r.returncode, 0)
        self.assertIn("open: 0", r.stdout)
        self.assertIn("done: 0", r.stdout)
        self.assertIn("total: 0", r.stdout)

    def test_stats_with_tasks(self):
        """counts reflect actual task state"""
        self._run("add", "Task one")
        self._run("add", "Task two")
        self._run("add", "Task three")
        self._run("done", "2")
        r = self._run("stats")
        self.assertEqual(r.returncode, 0)
        self.assertIn("open: 2", r.stdout)
        self.assertIn("done: 1", r.stdout)
        self.assertIn("total: 3", r.stdout)

    def test_stats_after_delete(self):
        """counts exclude deleted tasks"""
        self._run("add", "Task one")
        self._run("add", "Task two")
        self._run("delete", "2")
        r = self._run("stats")
        self.assertEqual(r.returncode, 0)
        self.assertIn("open: 1", r.stdout)
        self.assertIn("done: 0", r.stdout)
        self.assertIn("total: 1", r.stdout)


if __name__ == "__main__":
    unittest.main()
