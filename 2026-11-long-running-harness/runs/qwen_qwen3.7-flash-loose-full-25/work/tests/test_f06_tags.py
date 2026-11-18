import unittest
import subprocess
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestF06Tags(unittest.TestCase):
    def setUp(self):
        self.tmpdir = os.path.join(BASE_DIR, "test_tmp_f06")
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

    def test_add_single_tag(self):
        r = self.run_cmd("add", "work task", "--tag", "work")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        r2 = self.run_cmd("list")
        lines = r2.stdout.strip().split("\n")
        self.assertIn("#work", lines[0])

    def test_add_multiple_tags(self):
        r = self.run_cmd("add", "home task", "--tag", "work", "--tag", "home")
        self.assertEqual(r.returncode, 0)
        r2 = self.run_cmd("list")
        lines = r2.stdout.strip().split("\n")
        self.assertIn("#work #home", lines[0])

    def test_list_filter_by_tag(self):
        self.run_cmd("add", "work task", "--tag", "work")
        self.run_cmd("add", "personal task", "--tag", "personal")
        self.run_cmd("add", "another work task", "--tag", "work")
        r = self.run_cmd("list", "--tag", "work")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertIn("#work", line)

    def test_suffix_order_priority_then_tags(self):
        r = self.run_cmd("add", "task", "--priority", "high", "--tag", "work")
        self.assertEqual(r.returncode, 0)
        r2 = self.run_cmd("list")
        lines = r2.stdout.strip().split("\n")
        # Priority should come before tags
        self.assertIn("(high) #work", lines[0])

    def test_no_tasks_with_tag(self):
        self.run_cmd("add", "task", "--tag", "work")
        r = self.run_cmd("list", "--tag", "personal")
        self.assertEqual(r.stdout.strip(), "No tasks")

if __name__ == "__main__":
    unittest.main()
