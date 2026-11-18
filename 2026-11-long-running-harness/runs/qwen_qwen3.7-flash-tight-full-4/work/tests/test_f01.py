"""Tests for Feature F01: add - add TITLE creates an open task and prints 'Added <id>'."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Test the add command (F01)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_json = os.path.join(self.tmpdir, "tasks.json")
        # Copy tasks.py into the temp dir so subprocess can find it
        script_path = os.path.join(os.path.dirname(__file__), "..", "tasks.py")
        shutil.copy2(script_path, self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            cwd=self.tmpdir,
            capture_output=True, text=True
        )
        return result

    def test_add_single_task_prints_added_id(self):
        """Running add 'Buy milk' outputs 'Added 1'."""
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_multiple_tasks_incrementing_ids(self):
        """After two adds, ids are 1 and 2."""
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_add_creates_tasks_json(self):
        """tasks.json exists after adding a task."""
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(self.tasks_json))

    def test_add_creates_open_task(self):
        """The added task is not done."""
        self._run("add", "Buy milk")
        with open(self.tasks_json) as f:
            data = json.load(f)
        tasks = data["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertFalse(tasks[0]["done"])
        self.assertEqual(tasks[0]["title"], "Buy milk")
        self.assertEqual(tasks[0]["id"], 1)


if __name__ == "__main__":
    unittest.main()
