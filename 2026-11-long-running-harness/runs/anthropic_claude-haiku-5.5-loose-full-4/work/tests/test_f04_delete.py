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
        self.d = tempfile.mkdtemp()
        run(self.d, "add", "Buy milk")
        run(self.d, "add", "Walk dog")

    def test_delete_removes_task(self):
        r = run(self.d, "delete", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 2")
        r = run(self.d, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] Buy milk"])

    def test_ids_not_reused(self):
        run(self.d, "delete", "2")
        r = run(self.d, "add", "Feed cat")
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_unknown_id(self):
        r = run(self.d, "delete", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
