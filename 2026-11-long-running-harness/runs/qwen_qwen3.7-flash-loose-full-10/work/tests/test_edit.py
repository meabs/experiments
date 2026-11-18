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


class TestF08_Edit(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_edit_replaces_title(self):
        """edit 1 --title New title prints 'Edited 1'."""
        run('add', 'Old title', cwd=self.tmpdir)
        out, err, rc = run('edit', '1', '--title', 'New', 'title', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Edited 1')
        # Verify via list
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertEqual(out, '1 [ ] New title')

    def test_edit_preserves_other_fields(self):
        """Edit preserves priority, tags, due when only changing title."""
        run('add', 'Old title', '--priority', 'high', '--tag', 'work', '--due', '2026-03-01', cwd=self.tmpdir)
        out, err, rc = run('edit', '1', '--title', 'New title', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Edited 1')
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertEqual(out, '1 [ ] New title (high) #work due:2026-03-01')

    def test_edit_unknown_id_fails(self):
        """Unknown id -> 'No such task: <id>'."""
        run('add', 'task', cwd=self.tmpdir)
        out, err, rc = run('edit', '99', '--title', 'New', cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertEqual(err, 'No such task: 99')


if __name__ == '__main__':
    unittest.main()
