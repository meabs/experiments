"""Tests for feature F01: add command."""
import json
import os
import subprocess
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _run(self, *args):
        """Run tasks.py with given args in the temp directory."""
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_single_task(self):
        """Running: add 'Buy milk' -> Output is 'Added 1'"""
        result = self._run("add", "Buy milk")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")

    def test_add_second_task(self):
        """Running another add; output is 'Added 2'"""
        self._run("add", "Buy milk")
        result = self._run("add", "Walk dog")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after adding"""
        self._run("add", "Test task")
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_tasks_json_content(self):
        """Check tasks.json content after add"""
        self._run("add", "Buy milk")
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertIn(1, data["tasks"])
        self.assertEqual(data["tasks"][1]["title"], "Buy milk")
        self.assertFalse(data["tasks"][1]["done"])
        self.assertEqual(data["next_id"], 2)

    def test_add_multiword_title(self):
        """Title can be multiple words"""
        result = self._run("add", "Buy milk and eggs")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][1]["title"], "Buy milk and eggs")


if __name__ == "__main__":
    unittest.main()
