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


class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_prints_added_id(self):
        """add TITLE creates an open task and prints 'Added <id>'"""
        result = run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")

    def test_add_second_task_gets_id_2(self):
        """After another add; output is 'Added 2'"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        result = run_tasks(["add", "Walk dog"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after add"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_tasks_json_structure(self):
        """tasks.json has correct structure"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertIn("tasks", data)
        self.assertIn("next_id", data)
        self.assertEqual(data["next_id"], 2)
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"]["1"]["title"], "Buy milk")
        self.assertFalse(data["tasks"]["1"]["done"])


if __name__ == "__main__":
    unittest.main()
