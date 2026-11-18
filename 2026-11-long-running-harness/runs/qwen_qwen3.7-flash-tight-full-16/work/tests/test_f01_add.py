import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Feature F01: add TITLE creates an open task and prints 'Added <id>'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py into the temp dir
        src = os.path.join(os.path.dirname(__file__), "..", "tasks.py")
        shutil.copy(src, os.path.join(self.tmpdir, "tasks.py"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, "tasks.py"] + list(args),
            capture_output=True, text=True,
            cwd=self.tmpdir
        )
        return result

    def test_add_single_task(self):
        """Run: add 'Buy milk' -> Output is 'Added 1'"""
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_second_task(self):
        """Run another add; output is 'Added 2'"""
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after adding"""
        self._run("add", "Test")
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))

    def test_tasks_json_content(self):
        """tasks.json has correct content after add"""
        self._run("add", "Test task")
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertEqual(data["next_id"], 2)
        self.assertIn("1", data["tasks"])
        self.assertEqual(data["tasks"]["1"]["title"], "Test task")
        self.assertFalse(data["tasks"]["1"]["done"])


if __name__ == "__main__":
    unittest.main()
