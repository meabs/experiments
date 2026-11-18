import json, os, subprocess, sys, tempfile, unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

def run(*args, cwd=None):
    """Run tasks.py and return (stdout, stderr, returncode)."""
    if cwd is None:
        cwd = tempfile.mkdtemp()
    cmd = [sys.executable, TASKS_PY] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.cwd = tempfile.mkdtemp()

    def test_add_prints_added_id(self):
        out, err, rc = run('add', 'Buy milk', cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Added 1')

    def test_add_second_task_gets_id_2(self):
        run('add', 'Buy milk', cwd=self.cwd)
        out, _, _ = run('add', 'Walk dog', cwd=self.cwd)
        self.assertEqual(out, 'Added 2')

    def test_tasks_json_exists(self):
        run('add', 'Buy milk', cwd=self.cwd)
        self.assertTrue(os.path.exists(os.path.join(self.cwd, 'tasks.json')))

    def test_tasks_json_content(self):
        run('add', 'Buy milk', cwd=self.cwd)
        with open(os.path.join(self.cwd, 'tasks.json')) as f:
            data = json.load(f)
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['title'], 'Buy milk')
        self.assertFalse(data['tasks'][0]['done'])
        self.assertEqual(data['next_id'], 2)

    def test_add_multi_word_title(self):
        out, _, rc = run('add', 'Buy some milk', cwd=self.cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Added 1')
        # verify title stored correctly
        with open(os.path.join(self.cwd, 'tasks.json')) as f:
            data = json.load(f)
        self.assertEqual(data['tasks'][0]['title'], 'Buy some milk')

if __name__ == '__main__':
    unittest.main()
