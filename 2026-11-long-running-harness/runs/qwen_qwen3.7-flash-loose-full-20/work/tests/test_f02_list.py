import json, os, subprocess, sys, tempfile, unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

def run(*args, cwd=None):
    if cwd is None:
        cwd = tempfile.mkdtemp()
    cmd = [sys.executable, TASKS_PY] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

class TestF02List(unittest.TestCase):
    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def test_empty_list_prints_no_tasks(self):
        out, _, rc = run('list', cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'No tasks')

    def test_one_task_shows_line(self):
        run('add', 'Buy milk', cwd=self.cwd)
        out, _, rc = run('list', cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(out, '1 [ ] Buy milk')

    def test_two_tasks_in_order(self):
        run('add', 'Buy milk', cwd=self.cwd)
        run('add', 'Walk dog', cwd=self.cwd)
        out, _, _ = run('list', cwd=self.cwd)
        lines = out.split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [ ] Walk dog')

if __name__ == '__main__':
    unittest.main()
