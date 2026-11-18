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
    shutil.copy(src, dst)
    cmd = [sys.executable, "tasks.py"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestF02List(unittest.TestCase):
    """Feature 02: list - prints one line per task in id order, or 'No tasks'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_empty_list(self):
        """Empty list prints 'No tasks'"""
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "No tasks")
        self.assertEqual(err, "")

    def test_list_single_task(self):
        """One task shows as '1 [ ] title'"""
        run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "1 [ ] Buy milk")

    def test_list_two_tasks(self):
        """After two adds, lines are correct"""
        run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        run_task_manager(["add", "Walk dog"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_in_id_order(self):
        """Tasks are listed in ascending id order"""
        run_task_manager(["add", "Third"], cwd=self.tmpdir)
        run_task_manager(["add", "First"], cwd=self.tmpdir)
        run_task_manager(["add", "Second"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.split("\n")
        self.assertEqual(len(lines), 3)
        # Even though added 3, 1, 2, they should be ordered by id
        self.assertTrue(lines[0].startswith("1 "))
        self.assertTrue(lines[1].startswith("2 "))
        self.assertTrue(lines[2].startswith("3 "))


if __name__ == "__main__":
    unittest.main()
