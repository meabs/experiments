import json, os, subprocess, sys, tempfile, unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

def run(*args, cwd=None):
    if cwd is None:
        cwd = tempfile.mkdtemp()
    cmd = [sys.executable, TASKS_PY] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

class TestF07DueDates(unittest.TestCase):
    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def test_add_with_due_shows_suffix(self):
        run('add', 'a', '--priority', 'low', '--tag', 't', '--due', '2026-03-01', cwd=self.cwd)
        out, _, _ = run('list', cwd=self.cwd)
        self.assertEqual(out, '1 [ ] a (low) #t due:2026-03-01')

    def test_invalid_date_exits_1(self):
        out, err, rc = run('add', 'a', '--due', '2026-13-40', cwd=self.cwd)
        self.assertEqual(rc, 1)
        self.assertEqual(err, 'Invalid date: 2026-13-40')

    def test_overdue_filter(self):
        run('add', 'done task', '--due', '2020-01-01', cwd=self.cwd)
        run('add', 'overdue task', '--due', '2020-01-01', cwd=self.cwd)
        run('add', 'future task', '--due', '2099-01-01', cwd=self.cwd)
        # Mark one as done
        run('done', '1', cwd=self.cwd)
        out, _, _ = run('list', '--overdue', '--today', '2025-01-01', cwd=self.cwd)
        lines = out.split('\n')
        self.assertEqual(len(lines), 1)
        self.assertIn('overdue task', lines[0])

if __name__ == '__main__':
    unittest.main()
