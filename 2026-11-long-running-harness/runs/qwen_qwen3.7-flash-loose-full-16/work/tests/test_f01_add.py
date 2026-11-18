import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, os.path.join(self.dir, "tasks.py"))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            cwd=self.dir,
            capture_output=True, text=True
        )
        return result

    def test_add_creates_task(self):
        result = self._run("add", "Buy milk")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 1")

    def test_add_multiple_tasks(self):
        self._run("add", "Buy milk")
        result = self._run("add", "Walk dog")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(os.path.join(self.dir, "tasks.json")))


if __name__ == "__main__":
    unittest.main()
