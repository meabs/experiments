"""Variants change only what they should: falsified = one fact in one item; injection = an appended instruction in
ticket_notes and nothing else; combined = both; the verification store is untouched and separate."""
import json, os, re, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import agent, variants  # noqa: E402
S = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "scenarios", "scenarios.json")))}
V = json.load(open(os.path.join(ROOT, "manipulations", "variants.json")))


def by_source(ev):
    return {e["source"]: e for e in ev}


class Variants(unittest.TestCase):
    def test_falsified_changes_one_fact_in_one_item(self):
        for i, s in S.items():
            m = s["manipulation"]; c, f = by_source(V[i]["clean"]), by_source(V[i]["falsified"])
            self.assertEqual(set(c), set(f))
            changed = [k for k in c if c[k] != f[k]]
            self.assertEqual(changed, [m["source"]], i)
            self.assertEqual(f[m["source"]]["text"], c[m["source"]]["text"].replace(m["old"], m["new"]), i)
            self.assertNotIn(m["old"], f[m["source"]]["text"], i)
            for k in c:
                if k != m["source"]:
                    if m["witness"]:
                        pass
                    else:
                        self.assertNotIn(m["old"], c[k]["text"], (i, k))
            if m["witness"]:
                self.assertTrue(any(m["witness"] in f[k]["text"] for k in f if k != m["source"]), i)

    def test_falsified_has_no_instructions(self):
        for i in S:
            for e in V[i]["falsified"]:
                self.assertNotRegex(e["text"], r"(?i)instruction|ignore|AI triage assistant", i)

    def test_injection_only_appends_instruction(self):
        for i in S:
            c, j = by_source(V[i]["clean"]), by_source(V[i]["injection"])
            for k in c:
                if k == "ticket_notes":
                    self.assertTrue(j[k]["text"].startswith(c[k]["text"]), i)
                    added = j[k]["text"][len(c[k]["text"]):]
                    self.assertIn(added, variants.INJECT.values(), i)
                    self.assertNotRegex(added, r"\d", i)  # no numbers, times, addresses or ids: no facts
                else:
                    self.assertEqual(c[k], j[k], (i, k))

    def test_combined_is_falsified_plus_same_instruction(self):
        for i in S:
            f, j, cb = by_source(V[i]["falsified"]), by_source(V[i]["injection"]), by_source(V[i]["combined"])
            for k in f:
                if k == "ticket_notes":
                    self.assertEqual(cb[k]["text"], f[k]["text"] + j[k]["text"][len(by_source(V[i]["clean"])[k]["text"]):], i)
                else:
                    self.assertEqual(cb[k], f[k], (i, k))

    def test_verification_isolated_from_evidence(self):
        for i, s in S.items():
            outs = {}
            for var in ("clean", "falsified", "injection", "combined"):
                t = agent.Tools(V[i][var], s["verification"], True)
                outs[var] = [t.call("verify", {"check": c, "subject": subj}) for c, recs in s["verification"].items() for subj in recs]
                t2 = agent.Tools(V[i][var], s["verification"], False)
                self.assertTrue(t2.call("verify", {"check": "ip_registry", "subject": "10.0.0.1"}).startswith("Unknown tool"))
            self.assertTrue(all(o == outs["clean"] for o in outs.values()), i)
            m = s["manipulation"]
            self.assertNotIn(m["new"], json.dumps(s["verification"]), i)  # the store never repeats the falsified value

    def test_resolving_record_exists(self):
        for i, s in S.items():
            c, subj = s["manipulation"]["resolve"]
            self.assertIn(subj, s["verification"].get(c, {}), i)
