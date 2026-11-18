import json, os, subprocess, sys, tempfile, unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

def run(*args, cwd=None):
    if cwd is None:
        cwd = tempfile.mkdtemp()
    cmd = [sys.executable, TASKS_PY] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

class TestF04Delete(unittest.TestCase):
    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def test_delete_prints_deleted_id(self):
        run('add', 'Buy milk', cwd=self.cwd)
        out, _, rc = run('delete', '1', cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Deleted 1')

    def test_next_add_gets_new_id_not_reused(self):
        run('add', 'Buy milk', cwd=self.cwd)
        run('add', 'Walk dog', cwd=self.cwd)
        run('delete', '2', cwd=self.cwd)
        out, _, _ = run('add', 'Go shopping', cwd=self.cwd)
        self.assertEqual(out, 'Added 3')

    def test_delete_unknown_id_exits_1(self):
        run('add', 'Buy milk', cwd=self.cwd)
        out, err, rc = run('delete', '9', cwd=self.cwd)
        self.assertEqual(rc, 1)
        self.assertEqual(err, 'No such task: 9')

if __name__ == '__main__':
    unittest.main()
