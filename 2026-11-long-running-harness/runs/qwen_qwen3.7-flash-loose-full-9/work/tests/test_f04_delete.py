import json
import os
import subprocess
import tempfile
import shutil
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_tasks(args, cwd=None):
    """Run tasks.py with given args in a temp directory."""
    result = subprocess.run(
        ["python3", TASKS_PY] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result


class TestF04Delete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_delete_prints_deleted_id(self):
        """delete ID removes the task, prints 'Deleted <id>'"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        result = run_tasks(["delete", "1"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Deleted 1")

    def test_next_add_gets_new_id_not_reused(self):
        """After deleting task 2, next add gets id 3, not 2"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["add", "Walk dog"], cwd=self.tmpdir)
        run_tasks(["delete", "2"], cwd=self.tmpdir)
        result = run_tasks(["add", "New task"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 3")

    def test_unknown_id_exits_1(self):
        """Unknown id -> 'No such task: <id>' exit 1"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        result = run_tasks(["delete", "99"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 1)
        self.assertIn("No such task: 99", result.stderr)

    def test_delete_removes_from_store(self):
        """Delete removes the task from tasks.json"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["add", "Walk dog"], cwd=self.tmpdir)
        run_tasks(["delete", "2"], cwd=self.tmpdir)
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertNotIn("2", data["tasks"])
        self.assertEqual(len(data["tasks"]), 1)

    def test_delete_last_task(self):
        """Deleting the only remaining task leaves empty store"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["delete", "1"], cwd=self.tmpdir)
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "No tasks")


if __name__ == "__main__":
    unittest.main()
