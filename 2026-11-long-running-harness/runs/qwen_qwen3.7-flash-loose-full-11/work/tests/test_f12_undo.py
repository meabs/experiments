#!/usr/bin/env python3
"""Feature F12: undo - reverts last mutating command."""
import json, os, subprocess, sys, tempfile, unittest


class TestUndo(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        env = os.environ.copy()
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir, env=env)
        return r.stdout.strip(), r.stderr.strip(), r.returncode

    def _load_tasks(self):
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            return json.load(f)

    def test_undo_add(self):
        """F12: undo after add removes it and next add reuses that id"""
        self.run_cmd("add", "A")
        stdout, _, rc = self.run_cmd("undo")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Undone")
        data = self._load_tasks()
        self.assertEqual(len(data["tasks"]), 0)
        self.assertEqual(data["next_id"], 1)
        stdout, _, _ = self.run_cmd("add", "B")
        self.assertEqual(stdout, "Added 1")

    def test_undo_done(self):
        """F12: undo undoes done command"""
        self.run_cmd("add", "A")
        self.run_cmd("done", "1")
        stdout, _, _ = self.run_cmd("undo")
        self.assertEqual(stdout, "Undone")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] A")

    def test_undo_delete(self):
        """F12: undo undoes delete command"""
        self.run_cmd("add", "A")
        self.run_cmd("delete", "1")
        stdout, _, _ = self.run_cmd("undo")
        self.assertEqual(stdout, "Undone")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] A")

    def test_undo_edit(self):
        """F12: undo undoes edit command"""
        self.run_cmd("add", "Old")
        self.run_cmd("edit", "1", "--title", "New")
        stdout, _, _ = self.run_cmd("undo")
        self.assertEqual(stdout, "Undone")
        stdout, _, _ = self.run_cmd("list")
        self.assertEqual(stdout, "1 [ ] Old")

    def test_undo_nothing_to_undo(self):
        """F12: nothing to undo is an error"""
        stdout, stderr, rc = self.run_cmd("undo")
        self.assertEqual(rc, 1)
        self.assertIn("Nothing to undo", stderr)

    def test_undo_repeated(self):
        """F12: undo can be repeated to step further back"""
        self.run_cmd("add", "A")
        self.run_cmd("add", "B")
        self.run_cmd("undo")
        self.run_cmd("undo")
        data = self._load_tasks()
        self.assertEqual(len(data["tasks"]), 0)
        self.assertEqual(data["next_id"], 1)
