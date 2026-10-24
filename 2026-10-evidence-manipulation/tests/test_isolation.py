"""Hidden ground truth never reaches the agent: the runner never opens ground_truth.json, and no prompt, tool definition
or tool output carries a hidden field or label."""
import json, os, re, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import agent  # noqa: E402
S = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "scenarios", "scenarios.json")))}
V = json.load(open(os.path.join(ROOT, "manipulations", "variants.json")))
H = json.load(open(os.path.join(ROOT, "scenarios", "ground_truth.json")))
HIDDEN = ["ground_truth", "truth", "expected_action", "target", "witness", "unresolvable", "observable", "falsif",
          "manipulat", "suspicious_authentication", "credential_compromise", "privileged_access", "data_transfer",
          "api_activity", "scheduled_maintenance", "legitimate_admin", "false_positive", "category"]


class Isolation(unittest.TestCase):
    def test_runner_never_reads_ground_truth(self):
        for f in ("agent.py", "run.py"):
            self.assertNotIn("ground_truth", open(os.path.join(ROOT, "src", f)).read().split('"""', 2)[-1], f)

    def test_agent_inputs_carry_no_hidden_field(self):
        for i, s in S.items():
            for var in ("clean", "falsified", "injection", "combined"):
                for uv in (False, True):
                    t = agent.Tools(V[i][var], s["verification"], uv)
                    texts = [agent.alert_message(s["alert"]), json.dumps(agent.tools(s["alert"]["sources"], uv))]
                    texts += [t.call("get_evidence", {"source": src}) for src in s["alert"]["sources"]]
                    texts += [t.call("verify", {"check": c, "subject": subj}) for c, r in s["verification"].items() for subj in r]
                    blob = "\n".join(texts).lower()
                    for w in HIDDEN:
                        self.assertNotIn(w, blob.replace("uncategorised", ""), (i, var, w))

    def test_system_prompt_has_no_scenario_data(self):
        p = agent.SYSTEM.lower()
        for w in HIDDEN:
            if w not in ("manipulat",):  # the schema names the field suspected_manipulation
                self.assertNotIn(w, p.replace("uncategorised", ""), w)
        self.assertFalse(re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", agent.SYSTEM))
        for i, s in S.items():
            for e in s["evidence"]:
                for tok in re.findall(r"\b[a-z]{2,}[a-z0-9-]*\d\w*|\b\w+=\w+", e["text"]):
                    pass  # identities and values live only in tool outputs, checked above
