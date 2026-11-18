"""Tests for tasks.py - Feature F05: priority."""
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


class TestF05Priority(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_with_priority_high(self):
        """add with --priority high shows '(high)' suffix."""
        run_task(["add", "Task", "--priority", "high"], self.tmpdir)
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Task (high)")

    def test_add_with_priority_low(self):
        """add with --priority low shows '(low)' suffix."""
        run_task(["add", "Task", "--priority", "low"], self.tmpdir)
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Task (low)")

    def test_add_default_priority_medium(self):
        """Default priority is medium, no suffix."""
        run_task(["add", "Task"], self.tmpdir)
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Task")

    def test_invalid_priority_error(self):
        """Invalid priority value exits 1."""
        stdout, stderr, rc = run_task(["add", "Task", "--priority", "urgent"], self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("Invalid priority: urgent", stderr)

    def test_sort_by_priority(self):
        """list --sort priority orders high, medium, low, ties by id."""
        run_task(["add", "Low", "--priority", "low"], self.tmpdir)
        run_task(["add", "High", "--priority", "high"], self.tmpdir)
        run_task(["add", "Med"], self.tmpdir)
        stdout, _, _ = run_task(["list", "--sort", "priority"], self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("(high)", lines[0])
        self.assertNotIn("(medium)", lines[1])  # medium has no suffix
        self.assertIn("(low)", lines[2])


if __name__ == "__main__":
    unittest.main()
