import subprocess
import json
import os
import sys
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


def run(*args, cwd=None):
    """Run tasks.py with given args and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        [sys.executable, TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF06_Tags(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_add_with_tag_shows_suffix(self):
        """add a --tag work; list shows '1 [ ] a #work'"""
        out, err, rc = run('add', 'a', '--tag', 'work', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Added 1')
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertEqual(out, '1 [ ] a #work')

    def test_add_with_multiple_tags(self):
        """add a --tag work --tag home; list shows '1 [ ] a #work #home'"""
        out, err, rc = run('add', 'a', '--tag', 'work', '--tag', 'home', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Added 1')
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertEqual(out, '1 [ ] a #work #home')

    def test_list_filter_by_tag(self):
        """list --tag work shows only matching tasks"""
        run('add', 'task a', '--tag', 'work', cwd=self.tmpdir)
        run('add', 'task b', '--tag', 'home', cwd=self.tmpdir)
        run('add', 'task c', '--tag', 'work', cwd=self.tmpdir)
        
        out, _, _ = run('list', '--tag', 'work', cwd=self.tmpdir)
        lines = out.split('\n')
        self.assertEqual(len(lines), 2)
        self.assertIn('#work', lines[0])
        self.assertIn('#work', lines[1])

    def test_tag_suffix_after_priority(self):
        """suffix order: priority then tags"""
        out, err, rc = run('add', 'a', '--priority', 'high', '--tag', 'work', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertEqual(out, '1 [ ] a (high) #work')

    def test_add_without_tag_no_suffix(self):
        """Task without tags has no tag suffix."""
        out, err, rc = run('add', 'simple task', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertNotIn('#', out)
        self.assertEqual(out, '1 [ ] simple task')


if __name__ == '__main__':
    unittest.main()
