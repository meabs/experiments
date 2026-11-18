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


class TestF04_Delete(TasksTestBase):
    def test_delete_prints_deleted_and_removes_task(self):
        self.run_task('add', 'Buy milk')
        self.run_task('add', 'Walk dog')
        r = self.run_task('delete', '2')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Deleted 2')
        r = self.run_task('list')
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], '1 [ ] Buy milk')

    def test_next_add_gets_next_id_not_reused(self):
        self.run_task('add', 'Buy milk')
        self.run_task('add', 'Walk dog')
        self.run_task('delete', '2')
        r = self.run_task('add', 'Feed cat')
        self.assertEqual(r.stdout.strip(), 'Added 3')

    def test_delete_unknown_id_exits_1(self):
        r = self.run_task('delete', '9')
        self.assertEqual(r.returncode, 1)
        self.assertIn('No such task: 9', r.stderr)

    def test_delete_alone_works(self):
        self.run_task('add', 'Buy milk')
        self.run_task('delete', '1')
        r = self.run_task('list')
        self.assertEqual(r.stdout.strip(), 'No tasks')


if __name__ == '__main__':
    unittest.main()
