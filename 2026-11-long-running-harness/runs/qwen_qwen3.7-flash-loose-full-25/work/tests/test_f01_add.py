import unittest
import subprocess
import json
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.taskfile = os.path.join(self.tmpdir, "tasks.json")

    def tearDown(self):
        if os.path.exists(self.taskfile):
            os.remove(self.taskfile)
        os.rmdir(self.tmpdir)

    def run_cmd(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(BASE_DIR, "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_single_task(self):
        r = self.run_cmd("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_second_task(self):
        self.run_cmd("add", "Buy milk")
        r = self.run_cmd("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        self.run_cmd("add", "Buy milk")
        path = os.path.join(self.tmpdir, "tasks.json")
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["title"], "Buy milk")

if __name__ == "__main__":
    unittest.main()
