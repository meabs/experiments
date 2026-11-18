import subprocess, json, os, tempfile, shutil, unittest


class TasksTestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py to the temp directory so subprocess can find it
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


class TestF01_Add(TasksTestBase):
    def test_add_creates_task_and_prints_id(self):
        r = self.run_task('add', 'Buy milk')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 1')

    def test_add_second_task_gets_id_2(self):
        self.run_task('add', 'Buy milk')
        r = self.run_task('add', 'Walk dog')
        self.assertEqual(r.stdout.strip(), 'Added 2')

    def test_tasks_json_exists(self):
        self.run_task('add', 'Buy milk')
        self.assertTrue(os.path.exists('tasks.json'))


if __name__ == '__main__':
    unittest.main()
