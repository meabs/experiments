import unittest
import subprocess
import os
import json
import tempfile
import shutil


class TestF02List(unittest.TestCase):
    """Feature F02: list - prints one line per task in id order, or 'No tasks'"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        src = os.path.join(self.original_cwd, "tasks.py")
        dst = os.path.join(self.test_dir, "tasks.py")
        shutil.copy(src, dst)
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.test_dir
        )
        return result

    def test_empty_list_prints_no_tasks(self):
        """Empty list prints 'No tasks'"""
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_shows_open_task(self):
        """After add, list shows '[ ]' format"""
        self._run("add", "Buy milk")
        r = self._run("list")
        self.assertIn("[ ] Buy milk", r.stdout)

    def test_list_shows_done_task(self):
        """After done, list shows '[x]' format"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        self.assertIn("[x] Buy milk", r.stdout)
        self.assertNotIn("[ ] Buy milk", r.stdout)

    def test_list_orders_by_id(self):
        """Tasks are listed in id order"""
        self._run("add", "Third task")
        self._run("add", "First task")
        self._run("add", "Second task")
        r = self._run("list")
        lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
        self.assertEqual(lines[0], "1 [ ] Third task")
        self.assertEqual(lines[1], "2 [ ] First task")
        self.assertEqual(lines[2], "3 [ ] Second task")


if __name__ == "__main__":
    unittest.main()
