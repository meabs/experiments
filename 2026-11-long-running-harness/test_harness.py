import json
import tempfile
import unittest
from pathlib import Path

import harness as h

REF = (Path(__file__).parent / 'reference' / 'tasks.py').read_text()
STUB = "import sys\nprint('stub')\n"


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        h.RUNS = Path(self.tmp.name)
        h.WORK_ROOT = Path(self.tmp.name) / 'work'

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, cond, script, **kw):
        return h.run_one(h.Fake(script), cond, 'fake', 1, out_root=h.RUNS, **kw)

    def test_correct_solution_scores_12_and_is_not_premature(self):
        r = self.run_script('bare', [h.say(h.call('write_file', path='tasks.py', content=REF)),
                                     h.say(h.call('declare_done'))])
        self.assertEqual(r['final_passed'], 12)
        self.assertTrue(r['done_declared'])
        self.assertFalse(r['premature_victory'])
        self.assertEqual(r['broken_sessions'], 0)

    def test_stub_declared_done_is_premature_victory(self):
        r = self.run_script('bare', [h.say(h.call('write_file', path='tasks.py', content=STUB)),
                                     h.say(h.call('declare_done'))])
        self.assertTrue(r['premature_victory'])
        self.assertLess(r['final_passed'], 12)
        self.assertEqual(r['broken_sessions'], 1)  # stub fails the smoke check

    def test_session_ends_when_agent_stops_and_state_carries_over(self):
        script = [h.say(h.call('write_file', path='tasks.py', content=REF)), h.say(),  # session 1 ends
                  h.say(h.call('bash', command='ls')), h.say(h.call('declare_done'))]
        r = self.run_script('bare', script)
        self.assertEqual(r['sessions_used'], 2)
        self.assertEqual([s['reason'] for s in r['sessions']], ['stopped', 'declared_done'])
        self.assertEqual(r['sessions'][1]['passed'], 12)  # file written in session 1 still there

    def test_turn_cap_and_context_cap_end_sessions(self):
        looping = [h.say(h.call('bash', command='true')) for _ in range(10)]
        r = self.run_script('bare', looping, max_turns=3, max_sessions=2)
        self.assertEqual([s['reason'] for s in r['sessions']], ['turns', 'turns'])
        r = self.run_script('bare', [h.say(h.call('bash', command='true')) for _ in range(5)],
                            max_sessions=1, ctx_limit=1)
        self.assertEqual(r['sessions'][0]['reason'], 'context')

    def test_feature_list_edits_and_false_claims_are_counted(self):
        fl = json.loads((Path(__file__).parent / 'spec' / 'feature_list.json').read_text())
        fl[0]['description'] = 'changed'          # forbidden edit
        fl[1]['passes'] = True                    # claims F02 without implementing it
        fl.pop()                                  # removed entry
        script = [h.say(h.call('write_file', path='tasks.py', content=STUB),
                        h.call('write_file', path='feature_list.json', content=json.dumps(fl))),
                  h.say(h.call('declare_done'))]
        r = self.run_script('featurelist', script)
        self.assertEqual(r['fl_violations'], 2)
        self.assertEqual(r['false_claims'], 1)

    def test_only_passes_changes_are_allowed(self):
        fl = json.loads((Path(__file__).parent / 'spec' / 'feature_list.json').read_text())
        for e in fl:
            e['passes'] = True
        script = [h.say(h.call('write_file', path='tasks.py', content=REF),
                        h.call('write_file', path='feature_list.json', content=json.dumps(fl))),
                  h.say(h.call('declare_done'))]
        r = self.run_script('full', script)
        self.assertEqual(r['fl_violations'], 0)
        self.assertEqual(r['false_claims'], 0)

    def test_agent_cannot_see_hidden_tests_or_escape_workdir(self):
        r = self.run_script('bare', [
            h.say(h.call('bash', command='ls %s; ls /home' % (Path(__file__).parent / 'hidden')),
                  h.call('write_file', path='../escape.txt', content='x')),
            h.say(h.call('declare_done'))])
        t = [json.loads(l) for l in (h.RUNS / 'fake-bare-1' / 'transcript.jsonl').read_text().splitlines()]
        res = [x['result'] for x in t if x.get('tool') in ('bash', 'write_file')]
        self.assertNotIn('test_features.py', res[0])
        self.assertIn('outside working directory', res[1])

    def test_malformed_tool_arguments_do_not_end_the_run(self):
        bad = {'id': 'x1', 'type': 'function', 'function': {'name': 'bash', 'arguments': '{"command": '}}
        r = self.run_script('bare', [{'role': 'assistant', 'content': None, 'tool_calls': [bad]},
                                     h.say(h.call('declare_done'))])
        self.assertIsNone(r['error'])
        t = [json.loads(l) for l in (h.RUNS / 'fake-bare-1' / 'transcript.jsonl').read_text().splitlines()]
        self.assertIn('not valid JSON', [x for x in t if x.get('tool') == 'bash'][0]['result'])

    def test_full_condition_ships_init_sh_and_bare_does_not(self):
        h.setup_workdir('full', h.WORK_ROOT / 'a')
        h.setup_workdir('bare', h.WORK_ROOT / 'b')
        self.assertTrue((h.WORK_ROOT / 'a' / 'init.sh').exists())
        self.assertFalse((h.WORK_ROOT / 'b' / 'init.sh').exists())
        self.assertFalse((h.WORK_ROOT / 'b' / 'feature_list.json').exists())

    def test_budget_cap_stops_run(self):
        (h.RUNS / 'ledger.jsonl').write_text(json.dumps({'run': 'x', 'cost': 9.0}) + '\n')

        class Capped(h.Fake):
            def chat(self, messages):
                if h.spent() >= 8.0:
                    raise h.BudgetExceeded('cap')
                return super().chat(messages)
        r = h.run_one(Capped([h.say()]), 'bare', 'fake', 2, out_root=h.RUNS)
        self.assertIn('budget', r['error'])


if __name__ == '__main__':
    unittest.main()
