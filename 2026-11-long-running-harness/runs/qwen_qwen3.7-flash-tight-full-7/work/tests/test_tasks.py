import json
import os
import subprocess
import shutil
import tempfile
import unittest
import sys

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_PY = os.path.join(SCRIPT_DIR, "tasks.py")


def run_tasks(args, cwd=None):
    """Run tasks.py with given args, return result."""
    cmd = [sys.executable, TASKS_PY] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result


class TestF01_Add(unittest.TestCase):
    """Feature F01: add TITLE creates an open task and prints 'Added <id>'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, args):
        return run_tasks(args, cwd=self.tmpdir)

    def test_add_prints_id_1(self):
        r = self._run(["add", "Buy milk"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_prints_id_2(self):
        self._run(["add", "Buy milk"])
        r = self._run(["add", "Walk dog"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        self._run(["add", "Buy milk"])
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))


class TestF02_List(unittest.TestCase):
    """Feature F02: list prints one line per task in id order, or 'No tasks'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, args):
        return run_tasks(args, cwd=self.tmpdir)

    def test_empty_list(self):
        r = self._run(["list"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_two_tasks(self):
        self._run(["add", "Buy milk"])
        self._run(["add", "Walk dog"])
        r = self._run(["list"])
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


class TestF03_Done(unittest.TestCase):
    """Feature F03: done ID marks done, prints 'Done <id>'; unknown id -> stderr 'No such task: <id>', exit 1"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, args):
        return run_tasks(args, cwd=self.tmpdir)

    def test_done_prints(self):
        self._run(["add", "Buy milk"])
        r = self._run(["done", "1"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_done_shows_x(self):
        self._run(["add", "Buy milk"])
        self._run(["done", "1"])
        r = self._run(["list"])
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id(self):
        r = self._run(["done", "9"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


class TestF04_Delete(unittest.TestCase):
    """Feature F04: delete ID removes the task, prints 'Deleted <id>'; ids are never reused"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, args):
        return run_tasks(args, cwd=self.tmpdir)

    def test_delete_prints(self):
        self._run(["add", "Buy milk"])
        self._run(["add", "Walk dog"])
        r = self._run(["delete", "2"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 2")

    def test_next_add_gets_new_id(self):
        self._run(["add", "Buy milk"])
        self._run(["add", "Walk dog"])
        self._run(["delete", "2"])
        r = self._run(["add", "New task"])
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_delete_unknown_id(self):
        r = self._run(["delete", "9"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
