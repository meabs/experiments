"""Tests for tasks.py - Feature F12: undo command."""
import json
import os
import subprocess
import tempfile
import shutil
import unittest


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(_SCRIPT_DIR, "..", "tasks.py")


def run_task(args, cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    cmd = ["python3", SCRIPT_PATH] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF12Undo(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_undo_add_removes_task_and_reuses_id(self):
        """undo after add removes it and next add reuses that id."""
        run_task(["add", "Task"], self.tmpdir)
        stdout, _, _ = run_task(["undo"], self.tmpdir)
        self.assertEqual(stdout, "Undone")
        # Next add should get id 1 again
        stdout, _, _ = run_task(["add", "New task"], self.tmpdir)
        self.assertEqual(stdout, "Added 1")

    def test_undo_done_restores_state(self):
        """undo after done restores the task as not done."""
        run_task(["add", "Task"], self.tmpdir)
        run_task(["done", "1"], self.tmpdir)
        stdout, _, _ = run_task(["undo"], self.tmpdir)
        self.assertEqual(stdout, "Undone")
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertIn("[ ] Task", stdout)
        self.assertNotIn("[x]", stdout)

    def test_undo_delete_restores_task(self):
        """undo after delete restores the deleted task."""
        run_task(["add", "Task"], self.tmpdir)
        run_task(["delete", "1"], self.tmpdir)
        stdout, _, _ = run_task(["undo"], self.tmpdir)
        self.assertEqual(stdout, "Undone")
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Task")

    def test_undo_edit_restores_title(self):
        """undo after edit restores the old title."""
        run_task(["add", "Original"], self.tmpdir)
        run_task(["edit", "1", "--title", "Changed"], self.tmpdir)
        stdout, _, _ = run_task(["undo"], self.tmpdir)
        self.assertEqual(stdout, "Undone")
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertIn("Original", stdout)
        self.assertNotIn("Changed", stdout)

    def test_nothing_to_undo(self):
        """Nothing to undo -> exit 1 with error message."""
        stdout, stderr, rc = run_task(["undo"], self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "Nothing to undo")

    def test_repeatable_undo(self):
        """Repeated undo steps further back."""
        run_task(["add", "First"], self.tmpdir)
        run_task(["add", "Second"], self.tmpdir)
        run_task(["undo"], self.tmpdir)  # Undo 'Second'
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] First")
        run_task(["undo"], self.tmpdir)  # Undo 'First'
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "No tasks")

    def test_failed_commands_not_recorded(self):
        """Failed commands are not recorded in history."""
        run_task(["add", "Task"], self.tmpdir)
        # This will fail because task 9 doesn't exist
        run_task(["done", "9"])
        # The failed done should not be in history
        # So undo should undo the add, not a phantom done
        stdout, _, _ = run_task(["undo"], self.tmpdir)
        self.assertEqual(stdout, "Undone")
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "No tasks")

    def test_undo_across_runs(self):
        """Undo works across separate runs (history persists)."""
        run_task(["add", "Task"], self.tmpdir)
        run_task(["done", "1"], self.tmpdir)
        # Undo in a separate process invocation
        stdout, _, _ = run_task(["undo"], self.tmpdir)
        self.assertEqual(stdout, "Undone")
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertIn("[ ] Task", stdout)


if __name__ == "__main__":
    unittest.main()
