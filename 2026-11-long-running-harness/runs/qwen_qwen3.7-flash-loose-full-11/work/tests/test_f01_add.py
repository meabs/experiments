#!/usr/bin/env python3
"""Feature F01: add - adds tasks and prints 'Added <id>'."""
import json, os, subprocess, sys, tempfile, unittest


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def test_add_creates_task(self):
        stdout, stderr, rc = self.run_cmd("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        t = data["tasks"][0]
        self.assertEqual(t["id"], 1)
        self.assertEqual(t["title"], "Buy milk")
        self.assertFalse(t["done"])

    def test_add_multiple(self):
        self.run_cmd("add", "Buy milk")
        stdout, _, _ = self.run_cmd("add", "Walk dog")
        self.assertEqual(stdout, "Added 2")

    def test_add_with_priority_high(self):
        stdout, _, _ = self.run_cmd("add", "Urgent", "--priority", "high")
        self.assertEqual(stdout, "Added 1")
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            self.assertEqual(json.load(f)["tasks"][0]["priority"], "high")

    def test_add_default_priority_medium(self):
        self.run_cmd("add", "Normal")
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            self.assertEqual(json.load(f)["tasks"][0]["priority"], "medium")

    def test_add_invalid_priority(self):
        stdout, stderr, rc = self.run_cmd("add", "Bad", "--priority", "urgent")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid priority: urgent", stderr)

    def test_add_with_tags(self):
        self.run_cmd("add", "Task", "--tag", "work", "--tag", "home")
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            self.assertEqual(json.load(f)["tasks"][0]["tags"], ["work", "home"])

    def test_add_with_due_date(self):
        self.run_cmd("add", "Task", "--due", "2026-03-01")
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            self.assertEqual(json.load(f)["tasks"][0]["due"], "2026-03-01")

    def test_add_invalid_due_date(self):
        stdout, stderr, rc = self.run_cmd("add", "Task", "--due", "2026-13-40")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid date: 2026-13-40", stderr)
