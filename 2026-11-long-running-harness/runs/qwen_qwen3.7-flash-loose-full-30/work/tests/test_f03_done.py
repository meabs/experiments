import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


def run_task_manager(args, cwd=None):
    """Run tasks.py with given args and return (returncode, stdout, stderr)."""
    src = os.path.join(os.path.dirname(__file__), "..", "tasks.py")
    dst = os.path.join(cwd, "tasks.py") if cwd else "tasks.py"
    # Only copy if not already there
    if not os.path.exists(dst):
        shutil.copy(src, dst)
    cmd = [sys.executable, "tasks.py"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestF03Done(unittest.TestCase):
    """Feature 03: done - marks task done, prints 'Done <id>'; unknown id -> stderr error"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_done_prints_message(self):
        """done 2 prints 'Done 2'"""
        run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        run_task_manager(["add", "Walk dog"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["done", "2"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Done 2")

    def test_done_shows_as_done_in_list(self):
        """list shows '2 [x] Walk dog' after done"""
        run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        run_task_manager(["add", "Walk dog"], cwd=self.tmpdir)
        run_task_manager(["done", "2"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [x] Walk dog")

    def test_done_unknown_id_exits_1(self):
        """done 9 exits 1 with 'No such task: 9'"""
        rc, out, err = run_task_manager(["done", "9"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", err)

    def test_done_marks_only_that_task(self):
        """Only the specified task is marked done"""
        run_task_manager(["add", "First"], cwd=self.tmpdir)
        run_task_manager(["add", "Second"], cwd=self.tmpdir)
        run_task_manager(["add", "Third"], cwd=self.tmpdir)
        run_task_manager(["done", "2"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.split("\n")
        self.assertEqual(lines[0], "1 [ ] First")
        self.assertEqual(lines[1], "2 [x] Second")
        self.assertEqual(lines[2], "3 [ ] Third")


if __name__ == "__main__":
    unittest.main()
