import unittest
import subprocess
import shutil
import tempfile
import os
import json

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF01Add(unittest.TestCase):
    """Feature F01: add - create tasks"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def run_cmd(self, *args):
        """Run tasks.py with given arguments."""
        result = subprocess.run(
            ["python3", TASKS_PY] + list(args),
            capture_output=True, text=True
        )
        return result
    
    def test_add_creates_task_and_prints_id(self):
        """add TITLE creates an open task and prints 'Added <id>'"""
        r = self.run_cmd("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
    
    def test_second_add_gets_id_2(self):
        """Run another add; output is 'Added 2'"""
        self.run_cmd("add", "Buy milk")
        r = self.run_cmd("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")
    
    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after add"""
        self.run_cmd("add", "Buy milk")
        self.assertTrue(os.path.exists("tasks.json"))
    
    def test_added_task_is_open(self):
        """Task created by add starts as open (not done)"""
        self.run_cmd("add", "Buy milk")
        with open("tasks.json") as f:
            data = json.load(f)
        # JSON keys are strings
        task = data["tasks"]["1"]
        self.assertFalse(task["done"])
    
    def test_next_id_increments(self):
        """After two adds, next_id should be 3"""
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertEqual(data["next_id"], 3)


if __name__ == "__main__":
    unittest.main()
