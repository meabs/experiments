"""What features did each run choose? A text-only model codes each run's feature list from research.md (it sees only that
text, not the arm). Per feature: category, kind (core banking function | new capability | gimmick), whether a source is
named, and whether it is something a current mainstream UK bank app does not already offer. Then, per arm: features per
run, share with a source, share new, share gimmick, and overlap between runs (mean Jaccard of the sets of categories).
Descriptive; the coder is a model. Usage: python3 code_features.py <stage dir> -> features-coded.jsonl, analysis-features.md
"""
import itertools, json, re, sys
from pathlib import Path
import requests

CATS = ["payments", "balances_and_spending", "saving_and_goals", "credit_and_lending", "security_and_fraud", "ai_assistant",
        "data_sharing_open_banking", "identity_and_consent", "social_and_family", "rewards_and_perks", "accessibility_and_inclusion",
        "investing_and_crypto", "customisation_and_look", "support_and_help", "other"]
PROMPT = """Below is the research and feature list an AI designer wrote for a futuristic mobile banking app for a new generation
of users. Extract the chosen features (numbered F1, F2, ... or similar). For each, give:
- "id": its number as written
- "category": one of %s
- "kind": "core" (an ordinary banking function: pay, view balance, freeze card), "new" (a capability a mainstream UK bank app does not widely offer today) or "gimmick" (novelty with no clear customer need)
- "sourced": true if the text names a specific source or finding for it, else false

TEXT:
<<<
%s
>>>

Return only JSON: {"features": [{"id": "...", "category": "...", "kind": "...", "sourced": true|false}]}"""


def ask(text, key):
    body = {"model": "anthropic/claude-sonnet-5.5", "temperature": 0, "messages": [{"role": "user", "content": PROMPT % (CATS, text[:16000])}]}
    for _ in range(4):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=300, headers={"Authorization": f"Bearer {key}"})
            out = json.loads(re.search(r"\{.*\}", r.json()["choices"][0]["message"]["content"], re.S).group(0))
            if isinstance(out["features"], list):
                return out["features"]
        except Exception:
            pass
    return None


def main(stage):
    stage = Path(stage)
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    recs = []
    for rf in sorted(stage.glob("*/runs/F1/*/codex/*/artefacts/research.md")):
        arm, rep = rf.parts[-5], rf.parts[-3]
        feats = ask(rf.read_text(errors="replace"), key) or []
        recs.append({"arm": arm, "rep": rep, "features": feats})
    Path(stage, "features-coded.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    L = ["# FUT-1 feature choice (coded by a model from research.md; descriptive)", "",
         "| Arm | Features per run | Sourced | New capability | Gimmick | Core banking | Distinct categories per run | Overlap between runs (mean Jaccard of category sets; lower = more varied) |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for arm in "AB":
        rs = [r for r in recs if r["arm"] == arm]
        fs = [f for r in rs for f in r["features"]]
        n = max(1, len(fs))
        sets = [set(f["category"] for f in r["features"]) for r in rs]
        jac = [len(a & b) / max(1, len(a | b)) for a, b in itertools.combinations(sets, 2)]
        L.append(f"| {'A plain' if arm == 'A' else 'B factory'} | {len(fs) / max(1, len(rs)):.1f} | {sum(bool(f.get('sourced')) for f in fs) / n:.0%} | "
                 f"{sum(f.get('kind') == 'new' for f in fs) / n:.0%} | {sum(f.get('kind') == 'gimmick' for f in fs) / n:.0%} | "
                 f"{sum(f.get('kind') == 'core' for f in fs) / n:.0%} | {sum(len(s) for s in sets) / max(1, len(sets)):.1f} | {sum(jac) / max(1, len(jac)):.2f} |")
    L += ["", "Categories used, by arm (runs using each, of 5):", ""]
    for arm in "AB":
        c = {}
        for r in recs:
            if r["arm"] == arm:
                for cat in set(f["category"] for f in r["features"]):
                    c[cat] = c.get(cat, 0) + 1
        L.append(f"- {'plain' if arm == 'A' else 'factory'}: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items(), key=lambda x: -x[1])))
    Path(stage, "analysis-features.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1])
