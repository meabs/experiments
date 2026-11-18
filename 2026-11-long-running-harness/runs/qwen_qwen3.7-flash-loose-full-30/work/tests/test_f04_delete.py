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


class TestF04Delete(unittest.TestCase):
    """Feature 04: delete - removes task by ID, ids are never reused"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_delete_prints_message(self):
        """delete 2 prints 'Deleted 2'"""
        run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        run_task_manager(["add", "Walk dog"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["delete", "2"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Deleted 2")

    def test_next_add_gets_new_id(self):
        """next add gets id 3, not 2"""
        run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        run_task_manager(["add", "Walk dog"], cwd=self.tmpdir)
        run_task_manager(["delete", "2"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["add", "New task"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 3")

    def test_unknown_id_exits_1(self):
        """unknown id -> 'No such task: <id>' exit 1"""
        rc, out, err = run_task_manager(["delete", "9"], cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", err)

    def test_deleted_task_not_in_list(self):
        """After deleting, task is no longer listed"""
        run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        run_task_manager(["add", "Walk dog"], cwd=self.tmpdir)
        run_task_manager(["delete", "2"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] Buy milk")


if __name__ == "__main__":
    unittest.main()
