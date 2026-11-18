"""Tests for feature F01: add command."""
import json
import os
import subprocess
import sys
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Feature F01: add TITLE creates an open task and prints 'Added <id>'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        # Clean up any leftover files
        for f in ["tasks.json", "undo.json"]:
            if os.path.exists(f):
                os.remove(f)

    def tearDown(self):
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_add_single_task(self):
        """add 'Buy milk' -> 'Added 1', tasks.json exists."""
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        self.assertTrue(os.path.exists("tasks.json"))
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["title"], "Buy milk")
        self.assertFalse(data[0]["done"])

    def test_add_multiple_tasks(self):
        """Two adds produce 'Added 1' then 'Added 2'."""
        r1 = self._run("add", "Buy milk")
        self.assertEqual(r1.stdout.strip(), "Added 1")
        r2 = self._run("add", "Walk dog")
        self.assertEqual(r2.stdout.strip(), "Added 2")

    def test_add_creates_json(self):
        """tasks.json must be created after first add."""
        self.assertFalse(os.path.exists("tasks.json"))
        self._run("add", "Test")
        self.assertTrue(os.path.exists("tasks.json"))

    def test_add_with_priority_default(self):
        """Default priority is medium."""
        self._run("add", "Test")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(data[0]["priority"], "medium")


if __name__ == "__main__":
    unittest.main()
