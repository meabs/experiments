import subprocess
import os
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Test feature: add TITLE creates an open task and prints 'Added <id>'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py into the temp dir
        import shutil
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy(src, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_first_task(self):
        r = self._run("add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")

    def test_add_second_task(self):
        self._run("add", "Buy milk")
        r = self._run("add", "Walk dog")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_tasks_json_exists(self):
        self._run("add", "Buy milk")
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "tasks.json")))


if __name__ == "__main__":
    unittest.main()
