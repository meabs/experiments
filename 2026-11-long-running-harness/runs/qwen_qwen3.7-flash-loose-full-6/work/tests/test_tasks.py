import subprocess
import json
import os
import tempfile
import shutil
import unittest
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
TASKS_SRC = os.path.join(ROOT_DIR, 'tasks.py')

TASKS_CMD = [os.environ.get('PYTHON', 'python3')]

class BaseTaskTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.test_dir)
        # Copy tasks.py into the test dir
        shutil.copy2(TASKS_SRC, os.path.join(self.test_dir, 'tasks.py'))
        # Clean up any existing files
        for f in ['tasks.json', 'undo.json']:
            if os.path.exists(f):
                os.remove(f)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.test_dir)

    def run_cmd(self, *args, expect_fail=False):
        cmd = TASKS_CMD + ['tasks.py'] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if not expect_fail:
            self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def assert_output(self, result, expected):
        self.assertEqual(result[0], expected)


class TestAdd(BaseTaskTest):
    """F01: add TITLE creates an open task and prints 'Added <id>'"""

    def test_add_basic(self):
        out, err, rc = self.run_cmd('add', 'Buy milk')
        self.assert_output((out, err), 'Added 1')
        self.assertTrue(os.path.exists('tasks.json'))

    def test_add_multiple(self):
        self.run_cmd('add', 'Buy milk')
        out, err, rc = self.run_cmd('add', 'Walk dog')
        self.assert_output((out, err), 'Added 2')


class TestList(BaseTaskTest):
    """F02: list prints one line per task in id order, or 'No tasks'"""

    def test_empty_list(self):
        out, err, rc = self.run_cmd('list')
        self.assert_output((out, err), 'No tasks')

    def test_list_with_tasks(self):
        self.run_cmd('add', 'Buy milk')
        self.run_cmd('add', 'Walk dog')
        out, err, rc = self.run_cmd('list')
        lines = out.split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [ ] Walk dog')


class TestDone(BaseTaskTest):
    """F03: done ID marks done, prints 'Done <id>'; unknown id -> stderr 'No such task: <id>', exit 1"""

    def test_done_success(self):
        self.run_cmd('add', 'Buy milk')
        out, err, rc = self.run_cmd('done', '1')
        self.assert_output((out, err), 'Done 1')
        out, _, _ = self.run_cmd('list')
        self.assertIn('1 [x] Buy milk', out)

    def test_done_unknown_id(self):
        out, err, rc = self.run_cmd('done', '99', expect_fail=True)
        self.assertIn('No such task: 99', err)
        self.assertEqual(rc, 1)


class TestDelete(BaseTaskTest):
    """F04: delete ID removes the task, prints 'Deleted <id>'; ids are never reused"""

    def test_delete_success(self):
        self.run_cmd('add', 'Buy milk')
        out, err, rc = self.run_cmd('delete', '1')
        self.assert_output((out, err), 'Deleted 1')

    def test_delete_reuses_next_id(self):
        self.run_cmd('add', 'Buy milk')
        self.run_cmd('delete', '1')
        out, _, _ = self.run_cmd('add', 'Walk dog')
        self.assert_output((out, ''), 'Added 2')

    def test_delete_unknown_id(self):
        out, err, rc = self.run_cmd('delete', '99', expect_fail=True)
        self.assertIn('No such task: 99', err)
        self.assertEqual(rc, 1)


if __name__ == '__main__':
    unittest.main()
