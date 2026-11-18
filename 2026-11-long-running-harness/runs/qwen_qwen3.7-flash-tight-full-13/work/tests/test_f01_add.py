"""Tests for feature F01: add command."""
import json
import os
import subprocess
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_add_creates_task_prints_id(self):
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_second_add_gets_id_2(self):
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_created(self):
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists("tasks.json"))


if __name__ == "__main__":
    unittest.main()
