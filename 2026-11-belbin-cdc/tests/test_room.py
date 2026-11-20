"""Offline tests (mock agents): python3 -I -m unittest discover tests"""
import json, sqlite3, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import room


def fresh():
    room.DB = Path(tempfile.mkdtemp()) / "e.sqlite"


class T(unittest.TestCase):
    def test_nine_roles_from_the_page_and_reversed_in_rep2(self):
        r1, r2 = room.roles_for(1), room.roles_for(3)
        self.assertEqual(len({v["role"] for v in r1.values()}), 9)
        self.assertEqual([r1[a]["role"] for a in room.LETTERS], [r2[a]["role"] for a in room.LETTERS][::-1])
        self.assertEqual({v["category"] for v in r1.values()}, {"Social", "Thinking", "Task"})

    def test_forceful_paragraph_only_for_d_and_h_in_forceful_sessions(self):
        import re
        seen = {}
        orig = room.Mock
        class Spy:
            def __init__(self, a): self.a = a
            def turn(self, system, prompt):
                seen[self.a] = system; return "PASS", 1, 1
        room.Mock = Spy
        try:
            for sess in (1, 2):
                fresh(); seen.clear(); room.run_session(sess, "mock", 5, 1.0)
                for a in room.LETTERS:
                    has = "argue for them forcefully" in seen[a]
                    self.assertEqual(has, sess == 2 and a in ("D", "H"), (sess, a))
        finally: room.Mock = orig

    def test_task_mentions_cdc_and_bigquery(self):
        t = (room.ROOT / "arms" / "task.md").read_text()
        self.assertIn("BigQuery", t); self.assertIn("change data capture", t.lower())

    def test_persona_does_not_script_behaviour(self):
        for r in room.roles_for(1).values():
            self.assertIn("You are not told what to say", r["prompt"]); self.assertNotIn("you must", r["prompt"].lower())

    def test_mock_session_runs_and_ends(self):
        fresh(); stop, posted = room.run_session(1, "mock", 150, 2.0)
        self.assertIn(stop, ("agreed", "quiet", "message_cap")); self.assertGreater(posted, 5)

    def test_compare_and_swap_rejects_stale_edit(self):
        fresh()

        class Scripted:
            def __init__(self, a): self.a = a
            def turn(self, system, prompt):
                if "(version 0;" in prompt: return (f"DOC: draft by {self.a}", 10, 10)   # everybody drafts at once
                if "(version 1;" in prompt: return ("AGREE v1", 10, 10)
                return "PASS", 10, 10
        o = room.Mock; room.Mock = Scripted
        try: stop, _ = room.run_session(1, "mock", 150, 2.0)
        finally: room.Mock = o
        c = sqlite3.connect(room.DB)
        self.assertEqual(c.execute("select count(*) from events where kind='doc'").fetchone()[0], 1)
        self.assertEqual(c.execute("select count(*) from events where kind='doc_rejected'").fetchone()[0], 8)
        self.assertEqual(c.execute("select count(*) from events where kind='notice'").fetchone()[0], 8)
        self.assertEqual(stop, "agreed")

    def test_budget_and_cap(self):
        fresh(); stop, _ = room.run_session(2, "mock", 150, 0.0); self.assertEqual(stop, "budget")
        fresh(); stop, posted = room.run_session(2, "mock", 5, 2.0); self.assertIn(stop, ("message_cap", "agreed", "quiet"))


if __name__ == "__main__":
    unittest.main()
