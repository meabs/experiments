import unittest
import subprocess
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestF04Delete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = os.path.join(BASE_DIR, "test_tmp_f04")
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

    def test_delete_task(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        r = self.run_cmd("delete", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 2")

    def test_next_add_reuses_id(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        self.run_cmd("delete", "2")
        r = self.run_cmd("add", "Feed cat")
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_delete_unknown_id(self):
        r = self.run_cmd("delete", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)

if __name__ == "__main__":
    unittest.main()
