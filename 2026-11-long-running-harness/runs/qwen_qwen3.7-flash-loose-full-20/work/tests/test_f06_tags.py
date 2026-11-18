import json, os, subprocess, sys, tempfile, unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

def run(*args, cwd=None):
    if cwd is None:
        cwd = tempfile.mkdtemp()
    cmd = [sys.executable, TASKS_PY] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

class TestF06Tags(unittest.TestCase):
    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def test_add_with_tags_shows_suffix(self):
        run('add', 'a', '--tag', 'work', '--tag', 'home', cwd=self.cwd)
        out, _, _ = run('list', cwd=self.cwd)
        self.assertEqual(out, '1 [ ] a #work #home')

    def test_list_tag_filter(self):
        run('add', 'task1', '--tag', 'work', cwd=self.cwd)
        run('add', 'task2', '--tag', 'home', cwd=self.cwd)
        run('add', 'task3', '--tag', 'work', '--tag', 'home', cwd=self.cwd)
        out, _, _ = run('list', '--tag', 'work', cwd=self.cwd)
        lines = out.split('\n')
        self.assertEqual(len(lines), 2)
        self.assertIn('#work', lines[0])
        self.assertIn('#work', lines[1])

    def test_priority_then_tags_order(self):
        run('add', 'a', '--priority', 'low', '--tag', 't', cwd=self.cwd)
        out, _, _ = run('list', cwd=self.cwd)
        self.assertEqual(out, '1 [ ] a (low) #t')

if __name__ == '__main__':
    unittest.main()
