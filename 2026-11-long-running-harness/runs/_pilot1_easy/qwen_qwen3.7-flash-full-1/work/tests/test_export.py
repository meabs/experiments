"""Tests for tasks.py - Feature F10: export command."""
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


class TestF10Export(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_export_json_format(self):
        """export --format json prints JSON array of task objects."""
        run_task(["add", "Task", "--priority", "high", "--tag", "work"], self.tmpdir)
        stdout, _, _ = run_task(["export", "--format", "json"], self.tmpdir)
        data = json.loads(stdout)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["title"], "Task")
        self.assertEqual(data[0]["done"], False)
        self.assertEqual(data[0]["priority"], "high")
        self.assertEqual(data[0]["tags"], ["work"])
        self.assertIsNone(data[0]["due"])

    def test_export_csv_format(self):
        """export --format csv prints CSV with header and rows."""
        run_task(["add", "Task", "--priority", "low", "--tag", "a", "--tag", "b", "--due", "2026-01-01"], self.tmpdir)
        run_task(["done", "1"], self.tmpdir)
        stdout, _, _ = run_task(["export", "--format", "csv"], self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertEqual(lines[1], "1,Task,true,low,a;b,2026-01-01")

    def test_export_empty_store_json(self):
        """Empty store exports empty JSON array."""
        stdout, _, _ = run_task(["export", "--format", "json"], self.tmpdir)
        self.assertEqual(stdout, "[]")

    def test_export_empty_store_csv(self):
        """Empty store exports CSV with just the header."""
        stdout, _, _ = run_task(["export", "--format", "csv"], self.tmpdir)
        self.assertEqual(stdout, "id,title,done,priority,tags,due")

    def test_export_order_by_id(self):
        """Export outputs tasks in id order."""
        run_task(["add", "First"], self.tmpdir)
        run_task(["add", "Second"], self.tmpdir)
        run_task(["add", "Third"], self.tmpdir)
        stdout, _, _ = run_task(["export", "--format", "csv"], self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(lines[1].split(",")[0], "1")
        self.assertEqual(lines[2].split(",")[0], "2")
        self.assertEqual(lines[3].split(",")[0], "3")


if __name__ == "__main__":
    unittest.main()
