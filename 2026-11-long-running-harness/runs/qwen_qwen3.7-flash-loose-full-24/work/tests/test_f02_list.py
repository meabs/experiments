import subprocess
import os
import tempfile
import unittest


class TestF02List(unittest.TestCase):
    """Test feature: list prints one line per task in id order, or 'No tasks'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
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

    def test_empty_list(self):
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_after_adds(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


if __name__ == "__main__":
    unittest.main()
