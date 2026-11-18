import unittest
import subprocess
import shutil
import tempfile
import os
import json

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF02List(unittest.TestCase):
    """Feature F02: list - display tasks"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def run_cmd(self, *args):
        result = subprocess.run(
            ["python3", TASKS_PY] + list(args),
            capture_output=True, text=True
        )
        return result
    
    def test_empty_list_prints_no_tasks(self):
        """Empty list prints 'No tasks'"""
        r = self.run_cmd("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")
    
    def test_list_shows_tasks_in_id_order(self):
        """After two adds, lines are correct"""
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        r = self.run_cmd("list")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")
    
    def test_list_after_done_shows_checkmark(self):
        """After done, task shows [x]"""
        self.run_cmd("add", "Buy milk")
        self.run_cmd("done", "1")
        r = self.run_cmd("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")


if __name__ == "__main__":
    unittest.main()
