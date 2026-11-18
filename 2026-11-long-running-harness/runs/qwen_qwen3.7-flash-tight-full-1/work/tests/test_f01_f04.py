"""Tests for tasks.py - Features F01-F04"""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    """Feature F01: add"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_single_task(self):
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        self.assertTrue(os.path.exists("tasks.json"))

    def test_add_second_task(self):
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists("tasks.json"))
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertIn(1, data["tasks"])


class TestList(unittest.TestCase):
    """Feature F02: list"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        return subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_empty_list(self):
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_with_tasks(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


class TestDone(unittest.TestCase):
    """Feature F03: done"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        return subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_done_task(self):
        self._run("add", "Buy milk")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_done_marks_done(self):
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id(self):
        r = self._run("done", "99")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 99")


class TestDelete(unittest.TestCase):
    """Feature F04: delete"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        return subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_delete_task(self):
        self._run("add", "Buy milk")
        r = self._run("delete", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 1")

    def test_ids_never_reused(self):
        self._run("add", "Buy milk")
        self._run("delete", "1")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_delete_unknown_id(self):
        r = self._run("delete", "99")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 99")


if __name__ == "__main__":
    unittest.main()
