"""Tests for Feature F04: delete command."""
import os
import shutil
import subprocess
import tempfile
import unittest


class TestDelete(unittest.TestCase):
    """Test cases for the 'delete' command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy("tasks.py", self.tmpdir)
        self.tasks_json = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_delete_prints_deleted_id(self):
        """delete 2 prints 'Deleted 2'"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("delete", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 2")

    def test_next_add_gets_new_id_not_reused(self):
        """next add gets id 3, not 2"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "2")
        r = self._run("add", "New task")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_delete_unknown_id_exits_1(self):
        """unknown id -> 'No such task: <id>' exit 1"""
        r = self._run("delete", "99")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 99", r.stderr)

    def test_delete_removes_task_from_list(self):
        """deleted task no longer appears in list"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "1")
        r = self._run("list")
        self.assertNotIn("Buy milk", r.stdout)
        self.assertIn("Walk dog", r.stdout)

    def test_delete_only_task(self):
        """delete the only task leaves empty list"""
        self._run("add", "Only task")
        self._run("delete", "1")
        r = self._run("list")
        self.assertEqual(r.stdout.strip(), "No tasks")


if __name__ == "__main__":
    unittest.main()
