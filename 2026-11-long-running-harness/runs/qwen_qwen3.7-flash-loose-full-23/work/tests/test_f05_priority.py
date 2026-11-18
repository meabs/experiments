"""Tests for Feature F05: priority."""
import os
import shutil
import subprocess
import tempfile
import unittest


class TestPriority(unittest.TestCase):
    """Test cases for the 'priority' feature."""

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

    def test_add_with_priority_high_shows_suffix(self):
        """add a --priority high; list shows '1 [ ] a (high)'"""
        r = self._run("add", "a", "--priority", "high")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = self._run("list")
        self.assertIn("1 [ ] a (high)", r.stdout)

    def test_add_with_priority_low_shows_suffix(self):
        """add a --priority low; list shows '1 [ ] a (low)'"""
        r = self._run("add", "a", "--priority", "low")
        self.assertEqual(r.returncode, 0)
        r = self._run("list")
        self.assertIn("1 [ ] a (low)", r.stdout)

    def test_add_with_priority_medium_no_suffix(self):
        """add with medium priority has no suffix"""
        r = self._run("add", "a", "--priority", "medium")
        self.assertEqual(r.returncode, 0)
        r = self._run("list")
        # Should show "1 [ ] a" without any suffix
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a")

    def test_add_default_priority_is_medium(self):
        """add without --priority defaults to medium"""
        r = self._run("add", "a")
        self.assertEqual(r.returncode, 0)
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] a")

    def test_list_sort_priority_orders_high_medium_low(self):
        """list --sort priority orders high, medium, low, ties by id"""
        self._run("add", "C task", "--priority", "medium")
        self._run("add", "A task", "--priority", "high")
        self._run("add", "B task", "--priority", "low")
        r = self._run("list", "--sort", "priority")
        lines = [l for l in r.stdout.strip().split("\n")]
        # High first, then medium, then low
        self.assertIn("(high)", lines[0])
        self.assertIn("[ ] C task", lines[1])  # medium
        self.assertIn("(low)", lines[2])

    def test_invalid_priority_exits_1(self):
        """add --priority urgent exits 1 with 'Invalid priority: urgent'"""
        r = self._run("add", "Bad", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)

    def test_priority_and_tags_order(self):
        """suffix order: priority then tags"""
        r = self._run("add", "task", "--priority", "high", "--tag", "work")
        self.assertEqual(r.returncode, 0)
        r = self._run("list")
        self.assertIn("(high) #work", r.stdout)

    def test_priority_and_due_date_order(self):
        """suffix order: priority then due date"""
        r = self._run("add", "task", "--priority", "low", "--due", "2026-06-15")
        self.assertEqual(r.returncode, 0)
        r = self._run("list")
        self.assertIn("(low) due:2026-06-15", r.stdout)


if __name__ == "__main__":
    unittest.main()
