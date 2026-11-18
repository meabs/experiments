"""Tests for Feature F02: list command."""
import os
import shutil
import subprocess
import tempfile
import unittest


class TestList(unittest.TestCase):
    """Test cases for the 'list' command."""

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

    def test_empty_list_prints_no_tasks(self):
        """Empty list prints 'No tasks'"""
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_after_one_add(self):
        """After one add, list shows the task"""
        self._run("add", "Buy milk")
        r = self._run("list")
        self.assertIn("1 [ ] Buy milk", r.stdout)

    def test_list_after_two_adds(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_shows_done_task_with_x(self):
        """Done tasks show [x] instead of [ ]"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        self.assertIn("1 [x] Buy milk", r.stdout)

    def test_list_after_delete(self):
        """Deleted tasks do not appear in list"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "1")
        r = self._run("list")
        self.assertNotIn("Buy milk", r.stdout)
        self.assertIn("2 [ ] Walk dog", r.stdout)

    def test_ids_never_reused(self):
        """After deleting task 1, next add gets id 3, not 1"""
        self._run("add", "First")
        self._run("add", "Second")
        self._run("delete", "1")
        r = self._run("add", "Third")
        self.assertEqual(r.stdout.strip(), "Added 3")
        # Verify id 2 still exists
        r = self._run("list")
        self.assertIn("2 [ ] Second", r.stdout)

    def test_list_shows_priority_suffix(self):
        """List shows priority suffixes"""
        self._run("add", "High task", "--priority", "high")
        self._run("add", "Low task", "--priority", "low")
        self._run("add", "Med task", "--priority", "medium")
        r = self._run("list")
        self.assertIn("(high)", r.stdout)
        self.assertIn("(low)", r.stdout)
        # medium should have no suffix
        self.assertIn("3 [ ] Med task\n", r.stdout)

    def test_list_shows_tag_suffix(self):
        """List shows tag suffixes"""
        self._run("add", "Task", "--tag", "work", "--tag", "home")
        r = self._run("list")
        self.assertIn("#work #home", r.stdout)

    def test_list_shows_due_date_suffix(self):
        """List shows due date suffix"""
        self._run("add", "Task", "--due", "2026-06-15")
        r = self._run("list")
        self.assertIn("due:2026-06-15", r.stdout)


if __name__ == "__main__":
    unittest.main()
