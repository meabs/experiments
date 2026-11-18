"""Tests for F06: tags feature."""
import json
import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_tasks_in(tmpdir, *args):
    """Run tasks.py with given args in tmpdir, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=tmpdir
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestF06Tags(unittest.TestCase):

    def test_add_with_single_tag(self):
        """add TITLE --tag work should create task with tag."""
        tmpdir = tempfile.mkdtemp()
        rc, out, _ = run_tasks_in(tmpdir, "add", "Buy milk", "--tag", "work")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 1")
        # Check task line format
        rc2, out2, _ = run_tasks_in(tmpdir, "list")
        self.assertIn("#work", out2)

    def test_add_with_multiple_tags(self):
        """add TITLE --tag work --tag home should show both tags."""
        tmpdir = tempfile.mkdtemp()
        rc, out, _ = run_tasks_in(tmpdir, "add", "Buy milk", "--tag", "work", "--tag", "home")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "Added 1")
        rc2, out2, _ = run_tasks_in(tmpdir, "list")
        self.assertIn("#work", out2)
        self.assertIn("#home", out2)

    def test_tag_suffix_order(self):
        """Priority comes before tags in the suffix."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "Task", "--priority", "low", "--tag", "work")
        rc, out, _ = run_tasks_in(tmpdir, "list")
        # Should be "(low) #work" not "#work (low)"
        low_pos = out.find("(low)")
        hash_work_pos = out.find("#work")
        self.assertLess(low_pos, hash_work_pos)

    def test_list_filter_by_tag(self):
        """list --tag work shows only tasks with that tag."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "Work task", "--tag", "work")
        run_tasks_in(tmpdir, "add", "Home task", "--tag", "home")
        run_tasks_in(tmpdir, "add", "No tag task")
        rc, out, _ = run_tasks_in(tmpdir, "list", "--tag", "work")
        self.assertIn("Work task", out)
        self.assertNotIn("Home task", out)
        self.assertNotIn("No tag task", out)

    def test_list_no_match_tag_filter(self):
        """list --tag nonexistent shows No tasks."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "Some task", "--tag", "work")
        rc, out, _ = run_tasks_in(tmpdir, "list", "--tag", "nonexistent")
        self.assertIn("No tasks", out)

    def test_tags_stored_in_json(self):
        """Tags are stored correctly in tasks.json."""
        tmpdir = tempfile.mkdtemp()
        run_tasks_in(tmpdir, "add", "Test", "--tag", "a", "--tag", "b")
        with open(os.path.join(tmpdir, "tasks.json")) as f:
            data = json.load(f)
        task = data["tasks"]["1"]
        self.assertEqual(task["tags"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
