import unittest
import subprocess
import os
import json
import tempfile
import shutil


class TestF01Add(unittest.TestCase):
    """Feature F01: add - creates an open task and prints 'Added <id>'"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        # Copy tasks.py into test dir
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

    def test_add_creates_task_and_prints_id(self):
        """add 'Buy milk' outputs 'Added 1'"""
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_second_add_gets_next_id(self):
        """Second add gets id 2"""
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after add"""
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "tasks.json")))

    def test_added_task_is_open(self):
        """The added task shows as open [ ]"""
        self._run("add", "Buy milk")
        r = self._run("list")
        self.assertIn("[ ] Buy milk", r.stdout)


if __name__ == "__main__":
    unittest.main()
