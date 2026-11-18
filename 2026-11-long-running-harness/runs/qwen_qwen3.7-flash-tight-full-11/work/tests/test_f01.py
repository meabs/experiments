import json
import os
import subprocess
import shutil
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_task(*args, cwd=None):
    """Run tasks.py with given args and return (stdout, stderr, returncode)."""
    if cwd is None:
        cwd = tempfile.mkdtemp()
    result = subprocess.run(
        ["python3", TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout, result.stderr, result.returncode


class TestF01(unittest.TestCase):
    """Feature 1: add - creates an open task and prints 'Added <id>'"""

    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.cwd)

    def test_add_single_task(self):
        stdout, stderr, rc = run_task("add", "Buy milk", cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.strip(), "Added 1")

    def test_add_second_task(self):
        run_task("add", "Buy milk", cwd=self.cwd)
        stdout, stderr, rc = run_task("add", "Walk dog", cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        run_task("add", "Buy milk", cwd=self.cwd)
        self.assertTrue(os.path.exists(os.path.join(self.cwd, "tasks.json")))

    def test_ids_never_reused(self):
        # Add two tasks
        run_task("add", "Task A", cwd=self.cwd)
        run_task("add", "Task B", cwd=self.cwd)
        # Delete task 1
        run_task("delete", "1", cwd=self.cwd)
        # Next add should get id 3, not 1
        stdout, _, _ = run_task("add", "Task C", cwd=self.cwd)
        self.assertEqual(stdout.strip(), "Added 3")


if __name__ == "__main__":
    unittest.main()
