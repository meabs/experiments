import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        run(self.dir, "add", "Buy milk")
        run(self.dir, "add", "Walk dog")

    def test_delete_removes_task(self):
        r = run(self.dir, "delete", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "Deleted 2\n")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout, "1 [ ] Buy milk\n")

    def test_ids_not_reused(self):
        run(self.dir, "delete", "2")
        r = run(self.dir, "add", "New")
        self.assertEqual(r.stdout, "Added 3\n")

    def test_unknown_id(self):
        r = run(self.dir, "delete", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
