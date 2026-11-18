"""Tests for tasks.py - Feature F01: add command."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest


def run_tasks(cwd, args):
    """Run tasks.py with given args in a temp directory."""
    result = subprocess.run(
        ["python3", "tasks.py"] + args,
        cwd=cwd, capture_output=True, text=True
    )
    return result


class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py into the temp dir
        shutil.copy("tasks.py", self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_creates_task_and_prints_id(self):
        """add 'Buy milk' outputs 'Added 1'."""
        r = run_tasks(self.tmpdir, ["add", "Buy milk"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        self.assertEqual(r.stderr, "")

    def test_add_multiple_tasks_get_sequential_ids(self):
        """Second add gets id 2."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        r = run_tasks(self.tmpdir, ["add", "Walk dog"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_add_creates_tasks_json(self):
        """tasks.json exists after add."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_tasks_json_has_correct_structure(self):
        """tasks.json has correct structure after add."""
        run_tasks(self.tmpdir, ["add", "Buy milk"])
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertIn("tasks", data)
        self.assertIn("next_id", data)
        self.assertEqual(data["next_id"], 2)
        self.assertIn("1", data["tasks"])
        task = data["tasks"]["1"]
        self.assertEqual(task["title"], "Buy milk")
        self.assertFalse(task["done"])


if __name__ == "__main__":
    unittest.main()
