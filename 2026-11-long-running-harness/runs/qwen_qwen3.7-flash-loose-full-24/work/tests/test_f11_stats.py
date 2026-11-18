#!/usr/bin/env python3
"""Test feature: stats - open/done/total counts"""
import subprocess
import os
import tempfile
import shutil
import unittest


class TestF11Stats(unittest.TestCase):
    """Test feature: stats prints 'open: N', 'done: N', 'total: N'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy(src, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_stats_empty(self):
        """fresh store prints zeros"""
        r = self._run("stats")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines, ["open: 0", "done: 0", "total: 0"])

    def test_stats_with_open_tasks(self):
        """counts include open tasks"""
        self._run("add", "Task one")
        self._run("add", "Task two")
        r = self._run("stats")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines, ["open: 2", "done: 0", "total: 2"])

    def test_stats_with_done_tasks(self):
        """counts reflect done tasks correctly"""
        self._run("add", "Task one")
        self._run("add", "Task two")
        self._run("done", "1")
        r = self._run("stats")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines, ["open: 1", "done: 1", "total: 2"])

    def test_stats_excludes_deleted(self):
        """counts exclude deleted tasks"""
        self._run("add", "Task one")
        self._run("add", "Task two")
        self._run("delete", "1")
        self._run("done", "2")
        r = self._run("stats")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines, ["open: 0", "done: 1", "total: 1"])

    def test_stats_mixed(self):
        """mixed open, done, and deleted tasks"""
        self._run("add", "Open task")
        self._run("add", "Done task")
        self._run("add", "Will delete")
        self._run("done", "2")
        self._run("delete", "3")
        r = self._run("stats")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines, ["open: 1", "done: 1", "total: 2"])


if __name__ == "__main__":
    unittest.main()
