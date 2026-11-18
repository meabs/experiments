import subprocess
import json
import os
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Feature F01: add TITLE creates an open task and prints 'Added <id>'"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_py = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

    def _run(self, *args):
        result = subprocess.run(
            ['python3', self.tasks_py] + list(args),
            cwd=self.tmpdir,
            capture_output=True, text=True
        )
        return result

    def test_add_prints_id_1(self):
        r = self._run('add', 'Buy milk')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 1')

    def test_add_second_task_id_2(self):
        self._run('add', 'Buy milk')
        r = self._run('add', 'Walk dog')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 2')

    def test_tasks_json_exists(self):
        self._run('add', 'Buy milk')
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'tasks.json')))

    def test_tasks_json_structure(self):
        self._run('add', 'Buy milk')
        with open(os.path.join(self.tmpdir, 'tasks.json')) as f:
            data = json.load(f)
        self.assertIn('tasks', data)
        self.assertIn(1, data['tasks'])
        task = data['tasks'][1]
        self.assertEqual(task['title'], 'Buy milk')
        self.assertFalse(task['done'])
        self.assertEqual(data['next_id'], 2)


if __name__ == '__main__':
    unittest.main()
