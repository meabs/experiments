"""Tests for feature F05: priority."""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestPriority(unittest.TestCase):
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

    def test_add_high_priority_suffix(self):
        """add a --priority high; list shows '1 [ ] a (high)'."""
        r = self._run('add', 'a', '--priority', 'high')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run('list')
        self.assertEqual(r.stdout.strip(), '1 [ ] a (high)')

    def test_add_low_priority_suffix(self):
        """add b --priority low; list shows '1 [ ] b (low)'."""
        r = self._run('add', 'b', '--priority', 'low')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run('list')
        self.assertEqual(r.stdout.strip(), '1 [ ] b (low)')

    def test_add_medium_no_suffix(self):
        """add c --priority medium; list shows no suffix."""
        r = self._run('add', 'c', '--priority', 'medium')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run('list')
        self.assertEqual(r.stdout.strip(), '1 [ ] c')

    def test_default_is_medium(self):
        """Without --priority, task has medium priority (no suffix)."""
        r = self._run('add', 'default priority')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run('list')
        self.assertEqual(r.stdout.strip(), '1 [ ] default priority')

    def test_list_sort_by_priority(self):
        """list --sort priority orders high, medium, low, ties by id."""
        self._run('add', 'low_task', '--priority', 'low')
        self._run('add', 'med_task', '--priority', 'medium')
        self._run('add', 'high_task', '--priority', 'high')
        r = self._run('list', '--sort', 'priority')
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertIn('(high)', lines[0])
        # medium has no suffix, just plain title
        self.assertIn('med_task', lines[1])
        self.assertIn('(low)', lines[2])

    def test_invalid_priority_error(self):
        """add --priority urgent exits 1 with 'Invalid priority: urgent'."""
        r = self._run('add', 'bad', '--priority', 'urgent')
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), 'Invalid priority: urgent')

    def test_priority_stored_in_json(self):
        """tasks.json stores the priority value."""
        self._run('add', 'pinned', '--priority', 'high')
        with open(os.path.join(self.tmpdir, 'tasks.json')) as f:
            data = json.load(f)
        self.assertEqual(data['tasks'][0]['priority'], 'high')


if __name__ == '__main__':
    unittest.main()
