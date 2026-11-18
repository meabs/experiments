"""Tests for Feature F01: add command."""

import json
import os
import subprocess
import tempfile
import unittest


def run_task_manager(args, cwd):
    """Run tasks.py with given args in the given directory."""
    result = subprocess.run(
        ["python3", "tasks.py"] + args,
        capture_output=True, text=True, cwd=cwd
    )
    return result


class TestF01Add(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up any leftover tasks.json
        tasks_json = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(tasks_json):
            os.remove(tasks_json)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_creates_task_and_prints_id(self):
        """add 'Buy milk' outputs 'Added 1'."""
        result = run_task_manager(["add", "Buy milk"], self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")

    def test_add_second_task_gets_id_2(self):
        """Running another add gives 'Added 2'."""
        run_task_manager(["add", "Buy milk"], self.tmpdir)
        result = run_task_manager(["add", "Walk dog"], self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json is created after adding a task."""
        run_task_manager(["add", "Buy milk"], self.tmpdir)
        tasks_json = os.path.join(self.tmpdir, "tasks.json")
        self.assertTrue(os.path.exists(tasks_json))
        with open(tasks_json) as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["title"], "Buy milk")
        self.assertFalse(data["tasks"][0]["done"])

    def test_add_with_no_title_fails(self):
        """Adding without a title should fail."""
        result = run_task_manager(["add"], self.tmpdir)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
