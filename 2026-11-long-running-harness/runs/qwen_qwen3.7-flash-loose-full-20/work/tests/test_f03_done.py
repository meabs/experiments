import json, os, subprocess, sys, tempfile, unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

def run(*args, cwd=None):
    if cwd is None:
        cwd = tempfile.mkdtemp()
    cmd = [sys.executable, TASKS_PY] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

class TestF03Done(unittest.TestCase):
    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def test_done_prints_done_id(self):
        run('add', 'Buy milk', cwd=self.cwd)
        out, _, rc = run('done', '1', cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Done 1')

    def test_done_marks_task_as_x(self):
        run('add', 'Buy milk', cwd=self.cwd)
        run('done', '1', cwd=self.cwd)
        out, _, _ = run('list', cwd=self.cwd)
        self.assertEqual(out, '1 [x] Buy milk')

    def test_done_unknown_id_exits_1(self):
        run('add', 'Buy milk', cwd=self.cwd)
        out, err, rc = run('done', '9', cwd=self.cwd)
        self.assertEqual(rc, 1)
        self.assertEqual(err, 'No such task: 9')

if __name__ == '__main__':
    unittest.main()
