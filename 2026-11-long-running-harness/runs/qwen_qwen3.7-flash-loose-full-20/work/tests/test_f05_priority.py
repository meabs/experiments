import json, os, subprocess, sys, tempfile, unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

def run(*args, cwd=None):
    if cwd is None:
        cwd = tempfile.mkdtemp()
    cmd = [sys.executable, TASKS_PY] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

class TestF05Priority(unittest.TestCase):
    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def test_add_high_priority_shows_suffix(self):
        run('add', 'a', '--priority', 'high', cwd=self.cwd)
        out, _, _ = run('list', cwd=self.cwd)
        self.assertEqual(out, '1 [ ] a (high)')

    def test_add_low_priority_shows_suffix(self):
        run('add', 'a', '--priority', 'low', cwd=self.cwd)
        out, _, _ = run('list', cwd=self.cwd)
        self.assertEqual(out, '1 [ ] a (low)')

    def test_default_priority_medium_no_suffix(self):
        run('add', 'a', cwd=self.cwd)
        out, _, _ = run('list', cwd=self.cwd)
        self.assertEqual(out, '1 [ ] a')

    def test_list_sort_priority_orders_correctly(self):
        # Add tasks with different priorities and ids
        run('add', 'c', '--priority', 'low', cwd=self.cwd)   # id=1, low
        run('add', 'b', '--priority', 'high', cwd=self.cwd)  # id=2, high
        run('add', 'a', '--priority', 'medium', cwd=self.cwd) # id=3, medium
        out, _, _ = run('list', '--sort', 'priority', cwd=self.cwd)
        lines = out.split('\n')
        self.assertEqual(len(lines), 3)
        # high first (id=2), then medium (id=3), then low (id=1); ties by id
        self.assertIn('(high)', lines[0])
        self.assertNotIn('(medium)', lines[1])  # medium shows no suffix per spec
        self.assertIn('(low)', lines[2])

    def test_invalid_priority_exits_1(self):
        out, err, rc = run('add', 'a', '--priority', 'urgent', cwd=self.cwd)
        self.assertEqual(rc, 1)
        self.assertEqual(err, 'Invalid priority: urgent')

if __name__ == '__main__':
    unittest.main()
