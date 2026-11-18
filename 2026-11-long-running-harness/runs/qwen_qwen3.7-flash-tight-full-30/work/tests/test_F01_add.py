import json
import os
import subprocess
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Feature F01: add: add TITLE creates an open task and prints 'Added <id>'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        # Remove any existing data files
        for f in ['tasks.json', '.tasks_history.json', '.tasks_next_id']:
            if os.path.exists(f):
                os.remove(f)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        import shutil
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ['python3', 'tasks.py'] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_creates_task_and_prints_id(self):
        """Run: add 'Buy milk' -> Output is 'Added 1'"""
        r = self._run('add', 'Buy milk')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 1')

    def test_add_second_task_gets_id_2(self):
        """Run another add; output is 'Added 2'"""
        self._run('add', 'Buy milk')
        r = self._run('add', 'Walk dog')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 2')

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd"""
        self._run('add', 'Buy milk')
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'tasks.json')))

    def test_added_task_is_open(self):
        """Verify the task is stored as open (done=False)"""
        self._run('add', 'Buy milk')
        with open(os.path.join(self.tmpdir, 'tasks.json')) as f:
            tasks = json.load(f)
        self.assertEqual(len(tasks), 1)
        self.assertFalse(tasks[0]['done'])
        self.assertEqual(tasks[0]['title'], 'Buy milk')
        self.assertEqual(tasks[0]['id'], 1)


if __name__ == '__main__':
    unittest.main()
