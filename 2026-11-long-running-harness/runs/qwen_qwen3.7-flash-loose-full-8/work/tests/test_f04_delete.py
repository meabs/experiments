"""Tests for feature F04: delete command."""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy2(src, self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ['python3', 'tasks.py'] + list(args),
            cwd=self.tmpdir,
            capture_output=True, text=True
        )
        return result

    def test_delete_prints_id(self):
        """delete 1 prints 'Deleted 1'."""
        self._run('add', 'Buy milk')
        r = self._run('delete', '1')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Deleted 1')

    def test_delete_removes_task(self):
        """After delete, task is gone from list."""
        self._run('add', 'Buy milk')
        self._run('delete', '1')
        r = self._run('list')
        self.assertEqual(r.stdout.strip(), 'No tasks')

    def test_delete_unknown_id(self):
        """delete with unknown id prints error to stderr and exits 1."""
        r = self._run('delete', '999')
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 999", r.stderr)

    def test_delete_preserves_next_id(self):
        """After deleting a task, next add uses correct next id."""
        self._run('add', 'First')
        self._run('add', 'Second')
        self._run('delete', '1')
        r = self._run('add', 'Third')
        self.assertEqual(r.stdout.strip(), 'Added 3')

    def test_delete_done_task(self):
        """Can delete a done task."""
        self._run('add', 'Buy milk')
        self._run('done', '1')
        r = self._run('delete', '1')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Deleted 1')


if __name__ == '__main__':
    unittest.main()
