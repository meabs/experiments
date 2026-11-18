"""Tests for feature F04: delete command."""
import subprocess
import tempfile
import os
import unittest


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_delete_removes_task(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("delete", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 2")

    def test_next_add_gets_new_id(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "2")
        r = self._run("add", "New task")
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_delete_unknown_id_fails(self):
        r = self._run("delete", "99")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 99", r.stderr)


if __name__ == "__main__":
    unittest.main()
