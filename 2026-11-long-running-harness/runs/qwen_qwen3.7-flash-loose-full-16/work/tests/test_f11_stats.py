import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF11Stats(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, os.path.join(self.dir, "tasks.py"))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            cwd=self.dir,
            capture_output=True, text=True
        )
        return result

    def test_stats_fresh_store(self):
        result = self._run("stats")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "open: 0")
        self.assertEqual(lines[1], "done: 0")
        self.assertEqual(lines[2], "total: 0")

    def test_stats_with_open_tasks(self):
        self._run("add", "Task one")
        self._run("add", "Task two")
        result = self._run("stats")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "open: 2")
        self.assertEqual(lines[1], "done: 0")
        self.assertEqual(lines[2], "total: 2")

    def test_stats_after_done(self):
        self._run("add", "Task one")
        self._run("add", "Task two")
        self._run("done", "1")
        result = self._run("stats")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "open: 1")
        self.assertEqual(lines[1], "done: 1")
        self.assertEqual(lines[2], "total: 2")

    def test_stats_excludes_deleted_tasks(self):
        self._run("add", "Task one")
        self._run("add", "Task two")
        self._run("delete", "1")
        result = self._run("stats")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "open: 1")
        self.assertEqual(lines[1], "done: 0")
        self.assertEqual(lines[2], "total: 1")


if __name__ == "__main__":
    unittest.main()
