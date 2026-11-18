import json
import os
import subprocess
import tempfile
import shutil
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_tasks(args, cwd=None):
    """Run tasks.py with given args in a temp directory."""
    result = subprocess.run(
        ["python3", TASKS_PY] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result


class TestF05Priority(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_high_priority_shows_suffix(self):
        """add a --priority high; list shows '1 [ ] a (high)'"""
        result = run_tasks(["add", "a", "--priority", "high"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.stdout.strip(), "1 [ ] a (high)")

    def test_add_low_priority_shows_suffix(self):
        """add a --priority low; list shows '1 [ ] a (low)'"""
        result = run_tasks(["add", "a", "--priority", "low"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.stdout.strip(), "1 [ ] a (low)")

    def test_add_medium_priority_no_suffix(self):
        """Default medium priority shows no suffix"""
        result = run_tasks(["add", "a"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.stdout.strip(), "1 [ ] a")

    def test_add_explicit_medium_no_suffix(self):
        """Explicit --priority medium shows no suffix"""
        result = run_tasks(["add", "a", "--priority", "medium"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.stdout.strip(), "1 [ ] a")

    def test_invalid_priority_exits_1(self):
        """add --priority urgent exits 1 with 'Invalid priority: urgent'"""
        result = run_tasks(["add", "a", "--priority", "urgent"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Invalid priority: urgent", result.stderr)

    def test_sort_priority_orders_high_medium_low(self):
        """list --sort priority orders high, medium, low, ties by id"""
        run_tasks(["add", "c", "--priority", "low"], cwd=self.tmpdir)
        run_tasks(["add", "a", "--priority", "high"], cwd=self.tmpdir)
        run_tasks(["add", "b"], cwd=self.tmpdir)  # default medium
        result = run_tasks(["list", "--sort", "priority"], cwd=self.tmpdir)
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "2 [ ] a (high)")
        self.assertEqual(lines[1], "3 [ ] b")
        self.assertEqual(lines[2], "1 [ ] c (low)")

    def test_sort_priority_ties_by_id(self):
        """Ties in priority are broken by id order"""
        run_tasks(["add", "third", "--priority", "high"], cwd=self.tmpdir)
        run_tasks(["add", "first", "--priority", "high"], cwd=self.tmpdir)
        run_tasks(["add", "second", "--priority", "high"], cwd=self.tmpdir)
        result = run_tasks(["list", "--sort", "priority"], cwd=self.tmpdir)
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 3)
        # All have same priority, so sorted by id: 1, 2, 3
        self.assertEqual(lines[0], "1 [ ] third (high)")
        self.assertEqual(lines[1], "2 [ ] first (high)")
        self.assertEqual(lines[2], "3 [ ] second (high)")


if __name__ == "__main__":
    unittest.main()
