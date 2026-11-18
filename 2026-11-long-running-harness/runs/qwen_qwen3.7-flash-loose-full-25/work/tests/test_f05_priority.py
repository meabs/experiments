import unittest
import subprocess
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestF05Priority(unittest.TestCase):
    def setUp(self):
        self.tmpdir = os.path.join(BASE_DIR, "test_tmp_f05")
        os.makedirs(self.tmpdir, exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def run_cmd(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(BASE_DIR, "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_high_priority(self):
        r = self.run_cmd("add", "urgent task", "--priority", "high")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        r2 = self.run_cmd("list")
        lines = r2.stdout.strip().split("\n")
        self.assertIn("(high)", lines[0])

    def test_add_low_priority(self):
        r = self.run_cmd("add", "chore", "--priority", "low")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        r2 = self.run_cmd("list")
        lines = r2.stdout.strip().split("\n")
        self.assertIn("(low)", lines[0])

    def test_add_medium_no_suffix(self):
        r = self.run_cmd("add", "normal task", "--priority", "medium")
        self.assertEqual(r.returncode, 0)
        r2 = self.run_cmd("list")
        lines = r2.stdout.strip().split("\n")
        # Medium should have no suffix - just check it doesn't contain (high) or (low)
        self.assertNotIn("(high)", lines[0])
        self.assertNotIn("(low)", lines[0])

    def test_default_priority_is_medium(self):
        r = self.run_cmd("add", "default task")
        self.assertEqual(r.returncode, 0)
        r2 = self.run_cmd("list")
        lines = r2.stdout.strip().split("\n")
        self.assertNotIn("(high)", lines[0])
        self.assertNotIn("(low)", lines[0])

    def test_sort_by_priority(self):
        self.run_cmd("add", "low task", "--priority", "low")
        self.run_cmd("add", "high task", "--priority", "high")
        self.run_cmd("add", "med task", "--priority", "medium")
        r = self.run_cmd("list", "--sort", "priority")
        lines = r.stdout.strip().split("\n")
        self.assertIn("(high)", lines[0])
        self.assertNotIn("(high)", lines[1])  # medium has no suffix
        self.assertNotIn("(high)", lines[2])  # low has no (high)
        self.assertIn("(low)", lines[-1])

    def test_invalid_priority(self):
        r = self.run_cmd("add", "bad task", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)

    def test_sort_ties_by_id(self):
        self.run_cmd("add", "first high", "--priority", "high")
        self.run_cmd("add", "second high", "--priority", "high")
        self.run_cmd("add", "third high", "--priority", "high")
        r = self.run_cmd("list", "--sort", "priority")
        lines = r.stdout.strip().split("\n")
        # All are high priority, so order should be by id
        self.assertIn("first high", lines[0])
        self.assertIn("second high", lines[1])
        self.assertIn("third high", lines[2])

if __name__ == "__main__":
    unittest.main()
