import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


def run_task_manager(args, cwd=None):
    """Run tasks.py with given args and return (returncode, stdout, stderr)."""
    # Copy tasks.py into the temp dir so it can be executed there
    src = os.path.join(os.path.dirname(__file__), "..", "tasks.py")
    dst = os.path.join(cwd, "tasks.py") if cwd else "tasks.py"
    shutil.copy(src, dst)
    cmd = [sys.executable, "tasks.py"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestF01Add(unittest.TestCase):
    """Feature 01: add - add TITLE creates an open task and prints 'Added <id>'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up any files left behind
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_add_single_task(self):
        """add 'Buy milk' outputs 'Added 1'"""
        rc, out, err = run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 1")
        self.assertEqual(err, "")

    def test_add_multiple_tasks(self):
        """Each add gets the next id"""
        run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["add", "Walk dog"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists after adding a task"""
        run_task_manager(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_tasks_json_content(self):
        """tasks.json has correct structure"""
        run_task_manager(["add", "Test"], cwd=self.tmpdir)
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertIn("tasks", data)
        self.assertIn("next_id", data)
        # JSON keys are strings
        self.assertEqual(data["tasks"]["1"]["title"], "Test")
        self.assertFalse(data["tasks"]["1"]["done"])
        self.assertEqual(data["next_id"], 2)


if __name__ == "__main__":
    unittest.main()
