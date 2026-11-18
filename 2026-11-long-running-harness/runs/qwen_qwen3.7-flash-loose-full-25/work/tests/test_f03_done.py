import unittest
import subprocess
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestF03Done(unittest.TestCase):
    def setUp(self):
        self.tmpdir = os.path.join(BASE_DIR, "test_tmp_f03")
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

    def test_done_task(self):
        self.run_cmd("add", "Buy milk")
        r = self.run_cmd("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_done_shows_in_list(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("done", "1")
        r = self.run_cmd("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id(self):
        r = self.run_cmd("done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)

if __name__ == "__main__":
    unittest.main()
