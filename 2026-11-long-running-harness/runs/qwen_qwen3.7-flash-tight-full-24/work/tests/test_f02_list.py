"""Tests for feature F02: list command."""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestF02List(unittest.TestCase):
    """Test the list command - prints one line per task in id order, or 'No tasks'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.script = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ['python3', self.script] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_empty_list(self):
        """Empty list prints 'No tasks'."""
        r = self._run('list')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'No tasks')

    def test_list_two_tasks(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'."""
        self._run('add', 'Buy milk')
        r = self._run('add', 'Walk dog')
        self.assertEqual(r.returncode, 0)
        r2 = self._run('list')
        self.assertEqual(r2.returncode, 0)
        lines = r2.stdout.strip().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [ ] Walk dog')

    def test_list_shows_done_task(self):
        """Done tasks show [x]."""
        self._run('add', 'Buy milk')
        self._run('done', '1')
        r = self._run('list')
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [x] Buy milk')


if __name__ == '__main__':
    unittest.main()
