import subprocess, json, os, tempfile, shutil, unittest


class TasksTestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy2(src, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)
        if os.path.exists('tasks.json'):
            os.remove('tasks.json')

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmpdir)

    def run_task(self, *args):
        result = subprocess.run(
            ['python3', 'tasks.py'] + list(args),
            capture_output=True, text=True
        )
        return result


class TestF02_List(TasksTestBase):
    def test_empty_list(self):
        r = self.run_task('list')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'No tasks')

    def test_list_shows_tasks_in_id_order(self):
        self.run_task('add', 'Buy milk')
        self.run_task('add', 'Walk dog')
        r = self.run_task('list')
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [ ] Walk dog')

    def test_list_shows_done_status(self):
        self.run_task('add', 'Buy milk')
        self.run_task('done', '1')
        r = self.run_task('list')
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [x] Buy milk')


if __name__ == '__main__':
    unittest.main()
