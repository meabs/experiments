import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestList(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_empty(self):
        r = run(self.d, "list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_lines_in_id_order(self):
        run(self.d, "add", "Buy milk")
        run(self.d, "add", "Walk dog")
        r = run(self.d, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] Buy milk", "2 [ ] Walk dog"])


if __name__ == "__main__":
    unittest.main()
