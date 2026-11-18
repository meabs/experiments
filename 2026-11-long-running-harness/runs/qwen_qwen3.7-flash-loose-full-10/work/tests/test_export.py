import os
import sys
import json
import tempfile
import subprocess
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tasks.py')


def run(*args, cwd=None):
    """Run tasks.py with given args and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        [sys.executable, TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF10_ExportJson(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_empty_store_exports_empty_array(self):
        out, err, rc = run('export', '--format', 'json', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data, [])

    def test_json_contains_all_fields(self):
        run('add', 'Buy milk', '--priority', 'high', '--tag', 'work', '--due', '2024-01-01', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'json', cwd=self.tmpdir)
        data = json.loads(out)
        self.assertEqual(len(data), 1)
        task = data[0]
        self.assertIn('id', task)
        self.assertIn('title', task)
        self.assertIn('done', task)
        self.assertIn('priority', task)
        self.assertIn('tags', task)
        self.assertIn('due', task)
        self.assertEqual(task['id'], 1)
        self.assertEqual(task['title'], 'Buy milk')
        self.assertEqual(task['done'], False)
        self.assertEqual(task['priority'], 'high')
        self.assertEqual(task['tags'], ['work'])
        self.assertEqual(task['due'], '2024-01-01')

    def test_json_done_as_boolean(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        run('done', '1', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'json', cwd=self.tmpdir)
        data = json.loads(out)
        self.assertTrue(isinstance(data[0]['done'], bool))
        self.assertTrue(data[0]['done'])

    def test_json_null_due_when_none(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'json', cwd=self.tmpdir)
        data = json.loads(out)
        self.assertIsNone(data[0]['due'])

    def test_json_multiple_tasks_sorted_by_id(self):
        run('add', 'Third task', cwd=self.tmpdir)
        run('add', 'First task', cwd=self.tmpdir)
        run('add', 'Second task', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'json', cwd=self.tmpdir)
        data = json.loads(out)
        ids = [t['id'] for t in data]
        self.assertEqual(ids, [1, 2, 3])

    def test_json_tags_array(self):
        run('add', 'Buy stuff', '--tag', 'grocery', '--tag', 'home', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'json', cwd=self.tmpdir)
        data = json.loads(out)
        self.assertEqual(data[0]['tags'], ['grocery', 'home'])


class TestF10_ExportCsv(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_csv_header(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'csv', cwd=self.tmpdir)
        lines = out.split('\n')
        self.assertEqual(lines[0], 'id,title,done,priority,tags,due')

    def test_csv_empty_store(self):
        out, _, _ = run('export', '--format', 'csv', cwd=self.tmpdir)
        lines = out.split('\n')
        self.assertEqual(len(lines), 1)  # only header
        self.assertEqual(lines[0], 'id,title,done,priority,tags,due')

    def test_csv_done_as_true_false(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        run('done', '1', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'csv', cwd=self.tmpdir)
        lines = out.split('\n')
        # skip header
        row = lines[1].split(',')
        self.assertEqual(row[2], 'true')

    def test_csv_done_false_for_open(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'csv', cwd=self.tmpdir)
        lines = out.split('\n')
        row = lines[1].split(',')
        self.assertEqual(row[2], 'false')

    def test_csv_tags_joined_with_semicolon(self):
        run('add', 'Buy stuff', '--tag', 'grocery', '--tag', 'home', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'csv', cwd=self.tmpdir)
        lines = out.split('\n')
        row = lines[1].split(',')
        self.assertEqual(row[4], 'grocery;home')

    def test_csv_due_empty_when_none(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'csv', cwd=self.tmpdir)
        lines = out.split('\n')
        row = lines[1].split(',')
        self.assertEqual(row[5], '')

    def test_csv_due_has_value_when_set(self):
        run('add', 'Buy milk', '--due', '2024-06-15', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'csv', cwd=self.tmpdir)
        lines = out.split('\n')
        row = lines[1].split(',')
        self.assertEqual(row[5], '2024-06-15')

    def test_csv_default_priority_is_medium(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        out, _, _ = run('export', '--format', 'csv', cwd=self.tmpdir)
        lines = out.split('\n')
        row = lines[1].split(',')
        self.assertEqual(row[3], 'medium')


if __name__ == '__main__':
    unittest.main()
