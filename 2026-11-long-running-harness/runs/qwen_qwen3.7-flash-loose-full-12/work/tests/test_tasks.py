import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TaskManagerTestBase(unittest.TestCase):
    """Base class that sets up a temporary directory for each test."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py into the temp dir
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy2(src, self.tmpdir)
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def run_task(self, *args):
        """Run tasks.py with given arguments and return (stdout, stderr, returncode)."""
        result = subprocess.run(
            [sys.executable, "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF01_Add(TaskManagerTestBase):
    """Feature 1: add"""

    def test_add_creates_task(self):
        stdout, stderr, rc = self.run_task("add", "Buy milk")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_add_multiple_tasks(self):
        self.run_task("add", "Buy milk")
        stdout, stderr, rc = self.run_task("add", "Walk dog")
        self.assertEqual(stdout, "Added 2")

    def test_tasks_json_exists(self):
        self.run_task("add", "Buy milk")
        self.assertTrue(os.path.exists("tasks.json"))


class TestF02_List(TaskManagerTestBase):
    """Feature 2: list"""

    def test_empty_list(self):
        stdout, stderr, rc = self.run_task("list")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_shows_tasks(self):
        self.run_task("add", "Buy milk")
        self.run_task("add", "Walk dog")
        stdout, stderr, rc = self.run_task("list")
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


class TestF03_Done(TaskManagerTestBase):
    """Feature 3: done"""

    def test_done_marks_task(self):
        self.run_task("add", "Buy milk")
        stdout, stderr, rc = self.run_task("done", "1")
        self.assertEqual(stdout, "Done 1")
        out, _, _ = self.run_task("list")
        self.assertIn("1 [x] Buy milk", out)

    def test_done_unknown_id(self):
        stdout, stderr, rc = self.run_task("done", "99")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "No such task: 99")


class TestF04_Delete(TaskManagerTestBase):
    """Feature 4: delete"""

    def test_delete_removes_task(self):
        self.run_task("add", "Buy milk")
        stdout, stderr, rc = self.run_task("delete", "1")
        self.assertEqual(stdout, "Deleted 1")
        out, _, _ = self.run_task("list")
        self.assertEqual(out, "No tasks")

    def test_delete_reuses_next_id(self):
        self.run_task("add", "First")
        self.run_task("add", "Second")
        self.run_task("delete", "2")
        stdout, _, _ = self.run_task("add", "Third")
        self.assertEqual(stdout, "Added 3")

    def test_delete_unknown_id(self):
        stdout, stderr, rc = self.run_task("delete", "99")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "No such task: 99")


class TestF05_Priority(TaskManagerTestBase):
    """Feature 5: priority"""

    def test_priority_high(self):
        self.run_task("add", "Urgent task", "--priority", "high")
        out, _, _ = self.run_task("list")
        self.assertIn("(high)", out)

    def test_priority_low(self):
        self.run_task("add", "Low task", "--priority", "low")
        out, _, _ = self.run_task("list")
        self.assertIn("(low)", out)

    def test_priority_medium_no_suffix(self):
        self.run_task("add", "Med task", "--priority", "medium")
        out, _, _ = self.run_task("list")
        self.assertNotIn("(medium)", out)

    def test_default_priority(self):
        self.run_task("add", "Default task")
        out, _, _ = self.run_task("list")
        self.assertNotIn("(high)", out)
        self.assertNotIn("(low)", out)

    def test_invalid_priority(self):
        stdout, stderr, rc = self.run_task("add", "Bad task", "--priority", "urgent")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "Invalid priority: urgent")

    def test_sort_by_priority(self):
        self.run_task("add", "Low", "--priority", "low")
        self.run_task("add", "High", "--priority", "high")
        self.run_task("add", "Med", "--priority", "medium")
        out, _, _ = self.run_task("list", "--sort", "priority")
        lines = out.split("\n")
        self.assertIn("(high)", lines[0])
        self.assertIn("(low)", lines[2])


class TestF06_Tags(TaskManagerTestBase):
    """Feature 6: tags"""

    def test_tags_displayed(self):
        self.run_task("add", "Task", "--tag", "work", "--tag", "home")
        out, _, _ = self.run_task("list")
        self.assertIn("#work", out)
        self.assertIn("#home", out)

    def test_tag_filter(self):
        self.run_task("add", "Work task", "--tag", "work")
        self.run_task("add", "Home task", "--tag", "home")
        out, _, _ = self.run_task("list", "--tag", "work")
        self.assertIn("Work task", out)
        self.assertNotIn("Home task", out)


class TestF07_DueDates(TaskManagerTestBase):
    """Feature 7: due dates"""

    def test_due_date_displayed(self):
        self.run_task("add", "Task", "--due", "2026-03-01")
        out, _, _ = self.run_task("list")
        self.assertIn("due:2026-03-01", out)

    def test_invalid_date(self):
        stdout, stderr, rc = self.run_task("add", "Task", "--due", "2026-13-40")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "Invalid date: 2026-13-40")


class TestF08_Edit(TaskManagerTestBase):
    """Feature 8: edit"""

    def test_edit_title(self):
        self.run_task("add", "Old title")
        stdout, _, _ = self.run_task("edit", "1", "--title", "New title")
        self.assertEqual(stdout, "Edited 1")
        out, _, _ = self.run_task("list")
        self.assertIn("New title", out)

    def test_edit_unknown_id(self):
        stdout, stderr, rc = self.run_task("edit", "99", "--title", "New")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "No such task: 99")


class TestF09_Search(TaskManagerTestBase):
    """Feature 9: search"""

    def test_search_case_insensitive(self):
        self.run_task("add", "Buy Milk")
        self.run_task("add", "milkshake")
        out, _, _ = self.run_task("search", "milk")
        self.assertIn("Buy Milk", out)
        self.assertIn("milkshake", out)

    def test_search_no_match(self):
        self.run_task("add", "Buy milk")
        out, _, _ = self.run_task("search", "bread")
        self.assertEqual(out, "No matches")


class TestF10_Export(TaskManagerTestBase):
    """Feature 10: export"""

    def test_export_json(self):
        self.run_task("add", "Task1", "--priority", "high")
        stdout, _, _ = self.run_task("export", "--format", "json")
        data = json.loads(stdout)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["title"], "Task1")
        self.assertFalse(data[0]["done"])
        self.assertEqual(data[0]["priority"], "high")

    def test_export_csv(self):
        self.run_task("add", "Task1")
        stdout, _, _ = self.run_task("export", "--format", "csv")
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertIn("Task1", lines[1])

    def test_export_empty(self):
        stdout, _, _ = self.run_task("export", "--format", "json")
        self.assertEqual(json.loads(stdout), [])


class TestF11_Stats(TaskManagerTestBase):
    """Feature 11: stats"""

    def test_stats_fresh(self):
        out, _, _ = self.run_task("stats")
        self.assertEqual(out, "open: 0\ndone: 0\ntotal: 0")

    def test_stats_with_tasks(self):
        self.run_task("add", "Task1")
        self.run_task("add", "Task2")
        self.run_task("done", "1")
        out, _, _ = self.run_task("stats")
        self.assertEqual(out, "open: 1\ndone: 1\ntotal: 2")


class TestF12_Undo(TaskManagerTestBase):
    """Feature 12: undo"""

    def test_undo_after_add(self):
        self.run_task("add", "Task")
        stdout, _, _ = self.run_task("undo")
        self.assertEqual(stdout, "Undone")
        out, _, _ = self.run_task("list")
        self.assertEqual(out, "No tasks")

    def test_undo_reuses_id(self):
        self.run_task("add", "Task")
        self.run_task("undo")
        stdout, _, _ = self.run_task("add", "Task2")
        self.assertEqual(stdout, "Added 1")

    def test_nothing_to_undo(self):
        stdout, stderr, rc = self.run_task("undo")
        self.assertEqual(rc, 1)
        self.assertEqual(stderr, "Nothing to undo")

    def test_undo_persists_across_runs(self):
        self.run_task("add", "Task")
        # Run in a separate process
        subprocess.run([sys.executable, "tasks.py", "undo"], capture_output=True, cwd=self.tmpdir)
        out, _, _ = self.run_task("list")
        self.assertEqual(out, "No tasks")


if __name__ == "__main__":
    unittest.main()
