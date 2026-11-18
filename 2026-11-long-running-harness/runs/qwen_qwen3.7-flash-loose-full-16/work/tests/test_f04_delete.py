import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF04Delete(unittest.TestCase):
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

    def test_delete_removes_task(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        result = self._run("delete", "1")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Deleted 1")

    def test_next_add_uses_new_id(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "2")
        result = self._run("add", "Get coffee")
        self.assertEqual(result.stdout.strip(), "Added 3")

    def test_delete_unknown_id_exits_1(self):
        result = self._run("delete", "99")
        self.assertEqual(result.returncode, 1)
        self.assertIn("No such task: 99", result.stderr)


if __name__ == "__main__":
    unittest.main()
