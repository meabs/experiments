"""Offline tests: run with python3 -I -m unittest discover tests (from the experiment folder). Uses the mock agents only."""
import json, sqlite3, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import room


class RoomTest(unittest.TestCase):
    def run_session(self, n, **kw):
        d = Path(tempfile.mkdtemp()); room.DB = d / "e.sqlite"
        out = room.run_session(n, "mock", kw.get("max", 120), kw.get("budget", 2.0))
        return out, sqlite3.connect(room.DB)

    def test_session_completes_and_notes_written(self):
        (stop, posted), c = self.run_session(1)
        self.assertEqual(stop, "quiet"); self.assertGreater(posted, 5)
        self.assertEqual(c.execute("select count(*) from events where kind='notes'").fetchone()[0], 3)
        self.assertEqual(c.execute("select count(*) from events where kind='session_end'").fetchone()[0], 1)

    def test_message_cap_respected(self):
        (stop, posted), _ = self.run_session(1, max=10)
        self.assertEqual(stop, "message_cap"); self.assertLessEqual(posted, 13)  # three in-flight replies may land

    def test_budget_stops_session(self):
        (stop, _), _ = self.run_session(1, budget=0.0)
        self.assertIn(stop, ("budget",))

    def test_evidence_only_in_session_4_once(self):
        _, c = self.run_session(4)
        self.assertEqual(c.execute("select count(*) from events where kind='evidence'").fetchone()[0], 1)
        _, c = self.run_session(2)
        self.assertEqual(c.execute("select count(*) from events where kind='evidence'").fetchone()[0], 0)

    def test_model_swap_table(self):
        self.assertEqual([room.ASSIGN[s]["A"] for s in range(1, 6)], ["codex"] * 3 + ["claude"] * 2)
        self.assertEqual({room.ASSIGN[s]["B"] for s in range(1, 6)}, {"codex"})
        self.assertEqual([room.ASSIGN[s]["C"] for s in range(1, 6)], ["claude"] * 3 + ["codex"] * 2)

    def test_agents_see_session_numbers_not_db_ids(self):
        board = [(900, "scenario", "ROOM", "x", None), (905, "message", "A", "hi", None), (910, "message", "B", "yo", 2)]
        out = room.render(board, "A")
        self.assertIn("[2] Agent A (you): hi", out); self.assertIn("[3] Agent B -> 2: yo", out)

    def test_stale_flag_recorded(self):
        _, c = self.run_session(1)
        rows = c.execute("select json_extract(meta,'$.stale'), seen_upto, head from events where kind='message'").fetchall()
        for stale, seen, head in rows:
            self.assertEqual(bool(stale), head > seen)


if __name__ == "__main__":
    unittest.main()
