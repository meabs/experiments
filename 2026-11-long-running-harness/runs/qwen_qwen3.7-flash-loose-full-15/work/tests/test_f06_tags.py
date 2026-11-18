"""Tests for F06: tags feature"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PATH = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF06Tags(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, self.tmpdir)

    def _run(self, args):
        return subprocess.run(
            ['python3', 'tasks.py'] + args,
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_add_with_tags_shows_suffix(self):
        r = self._run(['add', 'task a', '--tag', 'work', '--tag', 'home'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] task a #work #home')

    def test_list_tag_filter(self):
        self._run(['add', 'task a', '--tag', 'work'])
        self._run(['add', 'task b', '--tag', 'home'])
        r = self._run(['list', '--tag', 'work'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertIn('#work', lines[0])

    def test_priority_before_tags_in_suffix_order(self):
        r = self._run(['add', 'task a', '--priority', 'low', '--tag', 't'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] task a (low) #t')

    def test_no_tags_no_suffix(self):
        r = self._run(['add', 'task a'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] task a')

    def test_single_tag(self):
        r = self._run(['add', 'task a', '--tag', 'urgent'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] task a #urgent')


if __name__ == '__main__':
    unittest.main()
