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


class TestF03(unittest.TestCase):
    """Feature 3: done - marks task done, prints 'Done <id>'; unknown id -> error"""

    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.cwd)

    def test_done_prints_message(self):
        run_task("add", "Buy milk", cwd=self.cwd)
        stdout, stderr, rc = run_task("done", "1", cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.strip(), "Done 1")

    def test_done_marks_task_done_in_list(self):
        run_task("add", "Buy milk", cwd=self.cwd)
        run_task("done", "1", cwd=self.cwd)
        stdout, _, _ = run_task("list", cwd=self.cwd)
        lines = stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        stdout, stderr, rc = run_task("done", "9", cwd=self.cwd)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", stderr)

    def test_done_twice_still_works(self):
        run_task("add", "Buy milk", cwd=self.cwd)
        stdout1, _, _ = run_task("done", "1", cwd=self.cwd)
        self.assertEqual(stdout1.strip(), "Done 1")
        # Done again should still work (task stays done)
        stdout2, _, _ = run_task("done", "1", cwd=self.cwd)
        self.assertEqual(stdout2.strip(), "Done 1")

    def test_done_multiple_tasks(self):
        run_task("add", "Task A", cwd=self.cwd)
        run_task("add", "Task B", cwd=self.cwd)
        run_task("done", "1", cwd=self.cwd)
        stdout, _, _ = run_task("list", cwd=self.cwd)
        lines = stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Task A")
        self.assertEqual(lines[1], "2 [ ] Task B")


if __name__ == "__main__":
    unittest.main()
