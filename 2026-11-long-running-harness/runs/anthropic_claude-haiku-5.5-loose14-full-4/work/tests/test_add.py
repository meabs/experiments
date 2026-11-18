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


class TestAddList(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_add_prints_id_and_creates_file(self):
        r = run(self.dir, "add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        self.assertTrue(os.path.exists(os.path.join(self.dir, "tasks.json")))
        r = run(self.dir, "add", "Walk dog")
        self.assertEqual(r.stdout.strip(), "Added 2")

    def test_list_empty(self):
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_after_adds(self):
        run(self.dir, "add", "Buy milk")
        run(self.dir, "add", "Walk dog")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] Buy milk", "2 [ ] Walk dog"])


if __name__ == "__main__":
    unittest.main()
