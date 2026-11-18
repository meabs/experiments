#!/usr/bin/env python3
"""Test feature: delete ID removes the task, prints 'Deleted <id>'; ids are never reused"""
import subprocess
import os
import tempfile
import shutil
import unittest


class TestF04Delete(unittest.TestCase):
    """Test feature: delete ID removes the task, prints 'Deleted <id>'; ids are never reused"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
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

    def test_delete_task(self):
        """delete 2 prints 'Deleted 2'"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("delete", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 2")

    def test_ids_never_reused(self):
        """next add gets id 3, not 2"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "2")
        r = self._run("add", "New task")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 3")

    def test_unknown_id(self):
        """unknown id -> 'No such task: <id>' exit 1"""
        r = self._run("delete", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)

    def test_delete_removes_from_list(self):
        """deleted task doesn't appear in list"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("delete", "1")
        r = self._run("list")
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "2 [ ] Walk dog")


if __name__ == "__main__":
    unittest.main()
