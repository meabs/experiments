import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF12Undo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, os.path.join(self.dir, "tasks.py"))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            cwd=self.dir,
            capture_output=True, text=True
        )
        return result

    def test_undo_add_removes_task_and_reuses_id(self):
        """After undoing add, task is gone and next add reuses that id."""
        result = self._run("add", "Task one")
        self.assertEqual(result.stdout.strip(), "Added 1")
        result = self._run("undo")
        self.assertEqual(result.stdout.strip(), "Undone")
        # After undo, task 1 should be gone
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "No tasks")
        # Next add should get id 1 again
        result = self._run("add", "Another task")
        self.assertEqual(result.stdout.strip(), "Added 1")

    def test_undo_done_restores_open_status(self):
        """Undo after done restores the task to open status."""
        self._run("add", "Task one")
        result = self._run("done", "1")
        self.assertEqual(result.stdout.strip(), "Done 1")
        result = self._run("list")
        self.assertIn("[x]", result.stdout)
        result = self._run("undo")
        self.assertEqual(result.stdout.strip(), "Undone")
        result = self._run("list")
        self.assertIn("[ ]", result.stdout)
        self.assertNotIn("[x]", result.stdout)

    def test_undo_delete_restores_deleted_task(self):
        """Undo after delete restores the deleted task at its original position."""
        self._run("add", "Task one")
        self._run("add", "Task two")
        self._run("add", "Task three")
        result = self._run("delete", "2")
        self.assertEqual(result.stdout.strip(), "Deleted 2")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("1 [ ] Task one", lines[0])
        self.assertIn("3 [ ] Task three", lines[1])
        result = self._run("undo")
        self.assertEqual(result.stdout.strip(), "Undone")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("1 [ ] Task one", lines[0])
        self.assertIn("2 [ ] Task two", lines[1])
        self.assertIn("3 [ ] Task three", lines[2])

    def test_undo_edit_restores_old_title(self):
        """Undo after edit restores the old title."""
        self._run("add", "Original title")
        result = self._run("edit", "1", "--title", "New Title")
        self.assertEqual(result.stdout.strip(), "Edited 1")
        result = self._run("list")
        self.assertIn("New Title", result.stdout)
        result = self._run("undo")
        self.assertEqual(result.stdout.strip(), "Undone")
        result = self._run("list")
        self.assertIn("Original title", result.stdout)
        self.assertNotIn("New Title", result.stdout)

    def test_multiple_undos_step_back(self):
        """Multiple undos step back through history in reverse order."""
        self._run("add", "Task A")
        self._run("add", "Task B")
        self._run("add", "Task C")
        # Undo Task C
        self._run("undo")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        # Undo Task B
        self._run("undo")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("Task A", lines[0])
        # Undo Task A
        self._run("undo")
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "No tasks")

    def test_undo_persists_across_runs(self):
        """Undo history survives between separate program invocations."""
        self._run("add", "Task one")
        self._run("add", "Task two")
        # New invocation: undo Task two
        result = self._run("undo")
        self.assertEqual(result.stdout.strip(), "Undone")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("Task one", lines[0])
        # New invocation: undo Task one
        result = self._run("undo")
        self.assertEqual(result.stdout.strip(), "Undone")
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "No tasks")

    def test_nothing_to_undo_error(self):
        """Undo with nothing to undo exits 1 and prints error."""
        result = self._run("undo")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Nothing to undo", result.stderr)

    def test_failed_commands_not_recorded(self):
        """Failed commands (e.g., unknown id) are not recorded in undo history."""
        self._run("add", "Task one")
        # Try to do an invalid command
        result = self._run("done", "999")
        self.assertEqual(result.returncode, 1)
        # Undo should only revert the add, not a phantom done
        result = self._run("undo")
        self.assertEqual(result.stdout.strip(), "Undone")
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "No tasks")

    def test_undo_preserves_all_task_attributes(self):
        """Undo restores all task attributes including priority, tags, due date."""
        result = self._run("add", "My task", "--priority", "high", "--tag", "work", "--due", "2026-12-25")
        self.assertEqual(result.stdout.strip(), "Added 1")
        self._run("undo")
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "No tasks")
        # Add it back and verify attributes survive
        result = self._run("add", "My task", "--priority", "high", "--tag", "work", "--due", "2026-12-25")
        self.assertEqual(result.stdout.strip(), "Added 1")
        result = self._run("list")
        line = result.stdout.strip()
        self.assertIn("(high)", line)
        self.assertIn("#work", line)
        self.assertIn("due:2026-12-25", line)

    def test_undo_after_mixed_operations(self):
        """Undo works correctly through a mix of add, done, edit, delete operations."""
        self._run("add", "Task A")
        self._run("add", "Task B")
        self._run("done", "1")
        self._run("edit", "2", "--title", "Updated B")
        self._run("delete", "1")
        # Current state: only "Updated B" with id 2
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("Updated B", lines[0])
        # Undo delete of Task A
        self._run("undo")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("1 [x] Task A", lines[0])
        self.assertIn("2 [ ] Updated B", lines[1])
        # Undo edit of Task B
        self._run("undo")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("1 [x] Task A", lines[0])
        self.assertIn("2 [ ] Task B", lines[1])
        # Undo done on Task A
        self._run("undo")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("1 [ ] Task A", lines[0])
        self.assertIn("2 [ ] Task B", lines[1])
        # Undo add of Task B
        self._run("undo")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("1 [ ] Task A", lines[0])
        # Undo add of Task A
        self._run("undo")
        result = self._run("list")
        self.assertEqual(result.stdout.strip(), "No tasks")

    def test_undo_next_id_restored(self):
        """Next ID is correctly restored after undo of add."""
        self._run("add", "Task A")
        self._run("add", "Task B")
        self._run("add", "Task C")
        # Undo Task C - next_id should go back to 3
        self._run("undo")
        result = self._run("add", "Task D")
        # Should get id 3 since that's what it was before adding C
        self.assertEqual(result.stdout.strip(), "Added 3")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("3 [ ] Task D", lines[2])

    def test_undo_of_delete_preserves_next_id(self):
        """Undo of delete restores next_id to what it was before the delete."""
        self._run("add", "Task A")
        self._run("add", "Task B")
        self._run("add", "Task C")
        # Delete B doesn't change next_id (still 4)
        self._run("delete", "2")
        # Undo delete - next_id goes back to 4
        self._run("undo")
        # Adding now gets id 4
        result = self._run("add", "Task D")
        self.assertEqual(result.stdout.strip(), "Added 4")


if __name__ == "__main__":
    unittest.main()
