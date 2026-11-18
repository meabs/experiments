"""Tests for feature F03: done command."""
import subprocess
import shutil
import tempfile
import os
import unittest


class TestF03Done(unittest.TestCase):
    """Test the done command - marks task done, prints Done <id>; unknown id -> error."""

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

    def test_done_prints_done_id(self):
        """done 2 prints 'Done 2'."""
        self._run('add', 'Buy milk')
        self._run('add', 'Walk dog')
        r = self._run('done', '2')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Done 2')

    def test_list_shows_done_task(self):
        """list shows '2 [x] Walk dog' after done."""
        self._run('add', 'Buy milk')
        self._run('add', 'Walk dog')
        self._run('done', '2')
        r = self._run('list')
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [x] Walk dog')

    def test_done_unknown_id(self):
        """done 9 exits 1 with 'No such task: 9'."""
        self._run('add', 'Buy milk')
        r = self._run('done', '9')
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), 'No such task: 9')


if __name__ == '__main__':
    unittest.main()
