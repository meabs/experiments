"""Tests for feature F03: done command."""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestDone(unittest.TestCase):
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

    def test_done_marks_task(self):
        """done 1 marks task 1 as done and prints 'Done 1'."""
        self._run('add', 'Buy milk')
        r = self._run('done', '1')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Done 1')

    def test_done_shows_x(self):
        """After done, list shows [x] for the task."""
        self._run('add', 'Buy milk')
        self._run('done', '1')
        r = self._run('list')
        self.assertIn('1 [x] Buy milk', r.stdout)

    def test_done_unknown_id(self):
        """done with unknown id prints error to stderr and exits 1."""
        r = self._run('done', '999')
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 999", r.stderr)

    def test_done_twice(self):
        """Running done twice on same task still works (second time also succeeds)."""
        self._run('add', 'Buy milk')
        self._run('done', '1')
        r = self._run('done', '1')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Done 1')


if __name__ == '__main__':
    unittest.main()
