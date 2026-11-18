"""Tests for tasks.py - Feature F01: add command."""
import json
import os
import subprocess
import tempfile
import shutil
import unittest


# Use absolute path so tests work regardless of cwd
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(_SCRIPT_DIR, "..", "tasks.py")


def run_task(args, cwd=None):
    """Run tasks.py with given arguments and return (stdout, stderr, returncode)."""
    if cwd is None:
        cwd = os.getcwd()
    cmd = ["python3", SCRIPT_PATH] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF01Add(unittest.TestCase):
    """Feature F01: add command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_creates_task_and_prints_id(self):
        """add 'Buy milk' prints 'Added 1'."""
        stdout, stderr, rc = run_task(["add", "Buy milk"], self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_add_multiple_tasks_get_incrementing_ids(self):
        """Running add again gets id 2."""
        run_task(["add", "Buy milk"], self.tmpdir)
        stdout, stderr, rc = run_task(["add", "Walk dog"], self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 2")

    def test_add_creates_tasks_json(self):
        """tasks.json exists after add."""
        run_task(["add", "Buy milk"], self.tmpdir)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_add_with_priority(self):
        """add with --priority flag."""
        stdout, stderr, rc = run_task(["add", "Task", "--priority", "high"], self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_add_with_tag(self):
        """add with --tag flag."""
        stdout, stderr, rc = run_task(["add", "Task", "--tag", "work"], self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")

    def test_add_with_due(self):
        """add with --due flag."""
        stdout, stderr, rc = run_task(["add", "Task", "--due", "2026-01-15"], self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Added 1")


class TestF02List(unittest.TestCase):
    """Feature F02: list command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_empty_list(self):
        """Empty list prints 'No tasks'."""
        # Create empty tasks.json
        data_path = os.path.join(self.tmpdir, "tasks.json")
        with open(data_path, "w") as f:
            json.dump({"tasks": {}, "next_id": 1, "history": []}, f)
        stdout, stderr, rc = run_task(["list"], self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "No tasks")

    def test_list_shows_tasks_in_order(self):
        """After two adds, lines show correct format."""
        run_task(["add", "Buy milk"], self.tmpdir)
        run_task(["add", "Walk dog"], self.tmpdir)
        stdout, stderr, rc = run_task(["list"], self.tmpdir)
        self.assertEqual(rc, 0)
        lines = stdout.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


class TestF03Done(unittest.TestCase):
    """Feature F03: done command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_done_marks_task(self):
        """done ID marks task done and prints 'Done <id>'."""
        run_task(["add", "Buy milk"], self.tmpdir)
        stdout, stderr, rc = run_task(["done", "1"], self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Done 1")

    def test_done_shows_checkmark(self):
        """list shows '[x]' for done task."""
        run_task(["add", "Buy milk"], self.tmpdir)
        run_task(["done", "1"], self.tmpdir)
        stdout, stderr, rc = run_task(["list"], self.tmpdir)
        self.assertIn("[x] Buy milk", stdout)

    def test_done_unknown_id_exits_1(self):
        """done unknown id -> exit 1 with error."""
        run_task(["add", "Buy milk"], self.tmpdir)
        stdout, stderr, rc = run_task(["done", "9"], self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", stderr)


class TestF04Delete(unittest.TestCase):
    """Feature F04: delete command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_delete_removes_task(self):
        """delete ID removes the task and prints 'Deleted <id>'."""
        run_task(["add", "Buy milk"], self.tmpdir)
        run_task(["add", "Walk dog"], self.tmpdir)
        stdout, stderr, rc = run_task(["delete", "2"], self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "Deleted 2")

    def test_next_add_does_not_reuse_deleted_id(self):
        """next add gets new id, not deleted one."""
        run_task(["add", "A"], self.tmpdir)
        run_task(["add", "B"], self.tmpdir)
        run_task(["delete", "2"], self.tmpdir)
        stdout, stderr, rc = run_task(["add", "C"], self.tmpdir)
        self.assertEqual(stdout, "Added 3")

    def test_delete_unknown_id_exits_1(self):
        """delete unknown id -> exit 1."""
        run_task(["add", "A"], self.tmpdir)
        stdout, stderr, rc = run_task(["delete", "9"], self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", stderr)


if __name__ == "__main__":
    unittest.main()
