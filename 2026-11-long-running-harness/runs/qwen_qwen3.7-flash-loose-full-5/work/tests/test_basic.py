"""Tests for tasks.py - F01 through F04."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    """F01: add TITLE creates an open task and prints 'Added <id>'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_file = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_first_task(self):
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_second_task(self):
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(self.tasks_file))

    def test_tasks_json_format(self):
        self._run("add", "Buy milk")
        with open(self.tasks_file) as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["title"], "Buy milk")
        self.assertFalse(data["tasks"][0]["done"])
        self.assertEqual(data["next_id"], 2)


class TestList(unittest.TestCase):
    """F02: list prints one line per task in id order, or 'No tasks'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_file = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_empty_list(self):
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_two_tasks(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


class TestDone(unittest.TestCase):
    """F03: done ID marks done, prints 'Done <id>'; unknown id -> stderr."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_file = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_done_prints(self):
        self._run("add", "Buy milk")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_done_shows_in_list(self):
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        self.assertIn("1 [x] Buy milk", r.stdout)

    def test_done_unknown_id(self):
        r = self._run("done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


class TestDelete(unittest.TestCase):
    """F04: delete removes task, prints 'Deleted <id>'; ids never reused."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_file = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_delete_prints(self):
        self._run("add", "Buy milk")
        r = self._run("delete", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 1")

    def test_next_id_after_delete(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "2")
        r = self._run("add", "New task")
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_delete_unknown_id(self):
        r = self._run("delete", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
