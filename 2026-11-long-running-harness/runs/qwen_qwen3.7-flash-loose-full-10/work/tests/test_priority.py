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


class TestF05_Priority(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_add_high_priority_shows_suffix(self):
        out, err, rc = run('add', 'task a', '--priority', 'high', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Added 1')
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertIn('(high)', out)
        self.assertEqual(out, '1 [ ] task a (high)')

    def test_add_low_priority_shows_suffix(self):
        out, err, rc = run('add', 'task b', '--priority', 'low', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertIn('(low)', out)
        self.assertEqual(out, '1 [ ] task b (low)')

    def test_add_medium_priority_no_suffix(self):
        out, err, rc = run('add', 'task c', '--priority', 'medium', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertNotIn('(', out)
        self.assertEqual(out, '1 [ ] task c')

    def test_default_priority_is_medium(self):
        out, err, rc = run('add', 'task d', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertNotIn('(', out)
        self.assertEqual(out, '1 [ ] task d')

    def test_invalid_priority_errors(self):
        out, err, rc = run('add', 'task e', '--priority', 'urgent', cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn('Invalid priority: urgent', err)

    def test_sort_by_priority_orders_correctly(self):
        run('add', 'c', '--priority', 'low', cwd=self.tmpdir)
        run('add', 'b', '--priority', 'high', cwd=self.tmpdir)
        run('add', 'a', '--priority', 'medium', cwd=self.tmpdir)
        out, _, _ = run('list', '--sort', 'priority', cwd=self.tmpdir)
        lines = out.split('\n')
        self.assertEqual(len(lines), 3)
        self.assertIn('(high)', lines[0])
        self.assertNotIn('(', lines[1])
        self.assertIn('(low)', lines[2])

    def test_sort_by_priority_ties_by_id(self):
        run('add', 'c', '--priority', 'high', cwd=self.tmpdir)
        run('add', 'a', '--priority', 'high', cwd=self.tmpdir)
        run('add', 'b', '--priority', 'high', cwd=self.tmpdir)
        out, _, _ = run('list', '--sort', 'priority', cwd=self.tmpdir)
        lines = out.split('\n')
        self.assertEqual(len(lines), 3)
        # All high priority, should be sorted by id ascending: 1(c), 2(a), 3(b)
        self.assertIn('1 [ ] c (high)', lines[0])
        self.assertIn('2 [ ] a (high)', lines[1])
        self.assertIn('3 [ ] b (high)', lines[2])


if __name__ == '__main__':
    unittest.main()
