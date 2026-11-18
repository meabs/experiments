"""Tests for tasks.py - Feature F06: tags."""
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


class TestF06Tags(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_with_tag(self):
        """add with --tag shows '#work' suffix."""
        run_task(["add", "Task", "--tag", "work"], self.tmpdir)
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Task #work")

    def test_add_multiple_tags(self):
        """add with multiple --tags shows '#work #home'."""
        run_task(["add", "Task", "--tag", "work", "--tag", "home"], self.tmpdir)
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Task #work #home")

    def test_list_filter_by_tag(self):
        """list --tag work shows only tasks with that tag."""
        run_task(["add", "A", "--tag", "work"], self.tmpdir)
        run_task(["add", "B", "--tag", "home"], self.tmpdir)
        run_task(["add", "C", "--tag", "work"], self.tmpdir)
        stdout, _, _ = run_task(["list", "--tag", "work"], self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("#work", lines[0])
        self.assertIn("#work", lines[1])

    def test_suffix_order_priority_then_tags(self):
        """Suffix order: priority then tags."""
        run_task(["add", "Task", "--priority", "high", "--tag", "work"], self.tmpdir)
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Task (high) #work")


if __name__ == "__main__":
    unittest.main()
