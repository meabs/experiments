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


class TestF02(unittest.TestCase):
    """Feature 2: list - prints one line per task in id order, or 'No tasks'"""

    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.cwd)

    def test_empty_list(self):
        stdout, _, rc = run_task("list", cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.strip(), "No tasks")

    def test_list_two_tasks(self):
        run_task("add", "Buy milk", cwd=self.cwd)
        run_task("add", "Walk dog", cwd=self.cwd)
        stdout, _, _ = run_task("list", cwd=self.cwd)
        lines = stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_order_is_by_id(self):
        run_task("add", "Task C", cwd=self.cwd)
        run_task("add", "Task A", cwd=self.cwd)
        run_task("add", "Task B", cwd=self.cwd)
        stdout, _, _ = run_task("list", cwd=self.cwd)
        lines = stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Task C")
        self.assertEqual(lines[1], "2 [ ] Task A")
        self.assertEqual(lines[2], "3 [ ] Task B")


if __name__ == "__main__":
    unittest.main()
