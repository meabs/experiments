import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd, capture_output=True, text=True)


class TestList(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_empty_list(self):
        r = run(self.dir, "list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_after_two_adds(self):
        run(self.dir, "add", "Buy milk")
        run(self.dir, "add", "Walk dog")
        r = run(self.dir, "list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] Buy milk", "2 [ ] Walk dog"])


if __name__ == "__main__":
    unittest.main()
