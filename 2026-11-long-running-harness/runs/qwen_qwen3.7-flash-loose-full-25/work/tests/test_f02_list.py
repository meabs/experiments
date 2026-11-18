import unittest
import subprocess
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestF02List(unittest.TestCase):
    def setUp(self):
        self.tmpdir = os.path.join(BASE_DIR, "test_tmp_f02")
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

    def test_empty_list(self):
        r = self.run_cmd("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_after_adds(self):
        self.run_cmd("add", "Buy milk")
        self.run_cmd("add", "Walk dog")
        r = self.run_cmd("list")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

if __name__ == "__main__":
    unittest.main()
