"""Tests for tasks.py - Feature F09: search command."""
import json
import os
import subprocess
import tempfile
import shutil
import unittest


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(_SCRIPT_DIR, "..", "tasks.py")


def run_task(args, cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    cmd = ["python3", SCRIPT_PATH] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF09Search(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_search_case_insensitive(self):
        """search TEXT matches case-insensitively."""
        run_task(["add", "Buy Milk"], self.tmpdir)
        run_task(["add", "milkshake recipe"], self.tmpdir)
        stdout, _, _ = run_task(["search", "milk"], self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("Buy Milk", lines[0])
        self.assertIn("milkshake", lines[1])

    def test_search_no_match(self):
        """No match prints 'No matches'."""
        run_task(["add", "Buy Milk"], self.tmpdir)
        stdout, _, _ = run_task(["search", "xyz"], self.tmpdir)
        self.assertEqual(stdout, "No matches")

    def test_search_in_id_order(self):
        """Search results are in id order."""
        run_task(["add", "First"], self.tmpdir)
        run_task(["add", "Second"], self.tmpdir)
        run_task(["add", "Third"], self.tmpdir)
        stdout, _, _ = run_task(["search", "first"], self.tmpdir)
        # Only "First" should match (case-insensitive substring)
        self.assertEqual(stdout, "1 [ ] First")


if __name__ == "__main__":
    unittest.main()
