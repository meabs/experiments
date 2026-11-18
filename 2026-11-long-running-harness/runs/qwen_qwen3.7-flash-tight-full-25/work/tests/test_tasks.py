"""Tests for tasks.py"""

import json
import os
import subprocess
import tempfile
import shutil
import unittest


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        for f in ["tasks.json", "tasks.undo.json"]:
            if os.path.exists(f):
                os.remove(f)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(self.original_cwd, "tasks.py")] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_add_prints_added_id(self):
        """add creates a task and prints 'Added <id>'."""
        result = self._run("add", "Buy milk")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")

    def test_add_second_task(self):
        """Second add gets id 2."""
        self._run("add", "Buy milk")
        result = self._run("add", "Walk dog")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json is created after adding."""
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists("tasks.json"))

    def test_title_stored_as_string(self):
        """Title is stored as a string, not a list."""
        self._run("add", "Buy milk")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["title"], "Buy milk")
        self.assertIsInstance(data["tasks"][0]["title"], str)

    def test_multiline_title(self):
        """Multi-word titles are joined correctly."""
        result = self._run("add", "Buy some milk")
        self.assertEqual(result.returncode, 0)
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["title"], "Buy some milk")


class TestList(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        for f in ["tasks.json", "tasks.undo.json"]:
            if os.path.exists(f):
                os.remove(f)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(self.original_cwd, "tasks.py")] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_empty_list(self):
        """Empty list prints 'No tasks'."""
        result = self._run("list")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "No tasks")

    def test_list_shows_tasks_in_order(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        result = self._run("list")
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_after_done(self):
        """Done tasks show [x]."""
        self._run("add", "Buy milk")
        self._run("done", "1")
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "1 [x] Buy milk")

    def test_list_after_delete(self):
        """Deleted tasks don't appear in list."""
        self._run("add", "Buy milk")
        self._run("delete", "1")
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "No tasks")


class TestDone(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        for f in ["tasks.json", "tasks.undo.json"]:
            if os.path.exists(f):
                os.remove(f)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(self.original_cwd, "tasks.py")] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_done_prints_done_id(self):
        """done 2 prints 'Done 2'."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        result = self._run("done", "2")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Done 2")

    def test_done_marks_task(self):
        """list shows the done task with [x]."""
        self._run("add", "Walk dog")
        self._run("done", "1")
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "1 [x] Walk dog")

    def test_done_unknown_id(self):
        """Unknown id -> stderr 'No such task: <id>', exit 1."""
        result = self._run("done", "9")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.strip(), "No such task: 9")


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        for f in ["tasks.json", "tasks.undo.json"]:
            if os.path.exists(f):
                os.remove(f)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(self.original_cwd, "tasks.py")] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_delete_prints_deleted_id(self):
        """delete 2 prints 'Deleted 2'."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        result = self._run("delete", "2")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Deleted 2")

    def test_next_add_uses_new_id(self):
        """Next add gets id 3, not 2."""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "2")
        result = self._run("add", "New task")
        self.assertEqual(result.stdout.strip(), "Added 3")

    def test_delete_unknown_id(self):
        """Unknown id -> 'No such task: <id>' exit 1."""
        result = self._run("delete", "99")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.strip(), "No such task: 99")


if __name__ == "__main__":
    unittest.main()
