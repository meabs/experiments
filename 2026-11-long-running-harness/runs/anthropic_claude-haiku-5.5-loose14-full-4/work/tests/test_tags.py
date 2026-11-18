import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.py"))


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestTags(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_tag_suffix(self):
        run(self.dir, "add", "a", "--tag", "work", "--tag", "home")
        run(self.dir, "add", "b", "--priority", "high", "--tag", "work")
        run(self.dir, "add", "c")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a #work #home", "2 [ ] b (high) #work", "3 [ ] c"])

    def test_list_by_tag(self):
        run(self.dir, "add", "a", "--tag", "work")
        run(self.dir, "add", "b", "--tag", "home")
        run(self.dir, "add", "c", "--tag", "work", "--tag", "home")
        r = run(self.dir, "list", "--tag", "work")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a #work", "3 [ ] c #work #home"])
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
