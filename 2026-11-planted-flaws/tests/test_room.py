"""Offline tests (mock agents): python3 -I -m unittest discover tests"""
import json, sqlite3, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import room

ROOT = room.ROOT


def fresh(): room.DB = Path(tempfile.mkdtemp()) / "e.sqlite"


class T(unittest.TestCase):
    def test_design_size_and_balance(self):
        conds = [c for c, r in room.SESSIONS.values()]
        self.assertEqual(len(conds), 20)
        for c in room.CONDS: self.assertEqual(conds.count(c), 5)

    def test_belbin_roles_rotate_across_letters(self):
        s = [k for k, (c, r) in room.SESSIONS.items() if c == "belbin"]
        a_roles = {room.roles_for(k)["A"]["role"] for k in s}
        self.assertEqual(len(a_roles), 5)
        for k in s: self.assertEqual(len({v["role"] for v in room.roles_for(k).values()}), 9)

    def test_eight_flaws_present_in_draft_and_documented(self):
        flaws = json.load(open(ROOT / "flaws.json")); draft = (ROOT / "arms" / "draft.md").read_text()
        self.assertEqual(len(flaws), 8)
        for key in ["zonal GKE Standard cluster", "80% utilisation", "guarantees that at least four", "fails over automatically to the replica",
                    "recovery point objective of zero", "regional external Application Load Balancer, whose single anycast", "enforces the primary key", "4.4 hours"]:
            self.assertIn(key, draft)
        for f in flaws: self.assertTrue(all(f[k] for k in ("id", "planted", "truth", "fixed_if")))

    def test_system_prompts_per_condition(self):
        seen = {}
        class Spy:
            def __init__(self, a): self.a = a
            def turn(self, system, prompt): seen.setdefault(self.a, system); return "PASS", 1, 1
        o = room.Mock; room.Mock = Spy
        try:
            for sess in (1, 2, 3, 4):
                fresh(); seen.clear(); room.run_session(sess, "mock", 3, 1.0)
                cond = room.SESSIONS[sess][0]
                for a in room.LETTERS:
                    if cond == "none": self.assertNotIn("temperament", seen[a]); self.assertNotIn("Belbin", seen[a])
                    if cond == "belbin": self.assertIn("Belbin", seen[a])
                    if cond == "sceptic": self.assertIn("sceptical by temperament", seen[a])
                    if cond == "agreeable": self.assertIn("agreeable and supportive by temperament", seen[a])
        finally: room.Mock = o

    def test_session_starts_with_draft_as_version_1(self):
        fresh(); room.run_session(1, "mock", 3, 1.0)
        c = sqlite3.connect(room.DB)
        d = c.execute("select agent,text from events where kind='doc' order by id limit 1").fetchone()
        self.assertEqual(d[0], "ROOM"); self.assertIn("design v1", d[1])

    def test_everyone_approving_version_1_ends_the_session(self):
        fresh()
        class Yes:
            def __init__(self, a): pass
            def turn(self, system, prompt): return "AGREE v1", 1, 1
        o = room.Mock; room.Mock = Yes
        try: stop, _ = room.run_session(1, "mock", 50, 1.0)
        finally: room.Mock = o
        self.assertEqual(stop, "agreed")

    def test_compare_and_swap_and_budget(self):
        fresh()
        class Ed:
            def __init__(self, a): pass
            def turn(self, system, prompt): return ("DOC: edited" if "(version 1;" in prompt else "AGREE v2"), 1, 1
        o = room.Mock; room.Mock = Ed
        try: room.run_session(1, "mock", 50, 1.0)
        finally: room.Mock = o
        c = sqlite3.connect(room.DB)
        self.assertEqual(c.execute("select count(*) from events where kind='doc'").fetchone()[0], 2)   # draft + one accepted edit
        self.assertEqual(c.execute("select count(*) from events where kind='doc_rejected'").fetchone()[0], 8)
        fresh(); self.assertEqual(room.run_session(1, "mock", 50, 0.0)[0], "budget")


if __name__ == "__main__":
    unittest.main()
