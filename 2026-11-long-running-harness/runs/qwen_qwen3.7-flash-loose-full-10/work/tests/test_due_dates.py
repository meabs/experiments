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


class TestF07_DueDates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_add_with_due_date_shows_suffix(self):
        """Task with due date shows 'due:YYYY-MM-DD' suffix."""
        out, err, rc = run('add', 'task a', '--due', '2026-03-01', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Added 1')
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertEqual(out, '1 [ ] task a due:2026-03-01')

    def test_invalid_date_errors(self):
        """--due 2026-13-40 exits 1 with 'Invalid date: 2026-13-40'."""
        out, err, rc = run('add', 'task b', '--due', '2026-13-40', cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn('Invalid date: 2026-13-40', err)

    def test_overdue_filters_open_tasks_only(self):
        """--overdue shows only OPEN tasks due before --today."""
        # Add an overdue task
        run('add', 'overdue task', '--due', '2020-01-01', cwd=self.tmpdir)
        # Add a future task
        run('add', 'future task', '--due', '2030-01-01', cwd=self.tmpdir)
        # Mark the FUTURE task as done, leaving the overdue task open
        run('done', '2', cwd=self.tmpdir)
        
        out, _, _ = run('list', '--overdue', '--today', '2025-01-01', cwd=self.tmpdir)
        lines = out.split('\n')
        self.assertEqual(len(lines), 1)
        self.assertIn('overdue task', lines[0])
        self.assertNotIn('future task', lines[0])

    def test_no_overdue_tasks(self):
        """No overdue tasks prints 'No tasks'."""
        run('add', 'future task', '--due', '2030-01-01', cwd=self.tmpdir)
        out, _, _ = run('list', '--overdue', '--today', '2025-01-01', cwd=self.tmpdir)
        self.assertEqual(out, 'No tasks')

    def test_due_after_priority_and_tags(self):
        """Suffix order: priority, then tags, then due date."""
        out, err, rc = run('add', 'a', '--priority', 'high', '--tag', 'work', '--due', '2026-03-01', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertEqual(out, '1 [ ] a (high) #work due:2026-03-01')


if __name__ == '__main__':
    unittest.main()
