import unittest
import subprocess
import shutil
import tempfile
import os
import json

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF03Done(unittest.TestCase):
    """Feature F03: done - mark tasks complete"""

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

    def test_done_prints_id(self):
        """done ID prints 'Done <id>'"""
        self.run_cmd("add", "Buy milk")
        r = self.run_cmd("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_done_shows_checkmark_in_list(self):
        """After done, list shows [x]"""
        self.run_cmd("add", "Buy milk")
        self.run_cmd("done", "1")
        r = self.run_cmd("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        """done 9 exits 1 with 'No such task: 9' to stderr"""
        self.run_cmd("add", "Buy milk")
        r = self.run_cmd("done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 9")

    def test_done_sets_done_flag(self):
        """Task done flag is set to True"""
        self.run_cmd("add", "Buy milk")
        self.run_cmd("done", "1")
        with open("tasks.json") as f:
            data = json.load(f)
        self.assertTrue(data["tasks"]["1"]["done"])

    def test_done_nonexistent_task(self):
        """done on a task that never existed"""
        r = self.run_cmd("done", "5")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 5")


if __name__ == "__main__":
    unittest.main()
