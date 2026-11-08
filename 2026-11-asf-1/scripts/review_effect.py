"""Review effect (README section 5, C only): hidden-test score before the first review vs after the last repair.

"Before the first review" is the last commit of the run's PR committed before Machinist started the first review
stage (from GitHub's PR commit list). Where the review's summary names the commit it reviewed, the two are checked
against each other. "After" is the run's graded final score. Runs with no review stage, or no commit before it,
have no before score and are listed. Writes results/main/review-effect.json.

Usage: python3 -I review_effect.py
"""
import json
import os
import re
import subprocess
from datetime import datetime

X = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(X, "results", "main")


def ts(s):
    """ISO time with any number of fractional digits (Machinist writes nanoseconds)."""
    s = re.sub(r"(\.\d{6})\d+", r"\1", s.replace("Z", "+00:00"))
    return datetime.fromisoformat(s)


def main():
    out = []
    for r in map(json.loads, open(os.path.join(MAIN, "bc-runs.jsonl"))):
        if r["arm"] != "C":
            continue
        rd = os.path.join(MAIN, "runs", r["ticket"], "C", "codex", str(r["rep"]))
        job = json.load(open(os.path.join(rd, "machinist-job.json")))
        revs = [x for x in job["runs"] if x["command"] == "review"]
        row = dict(ticket=r["ticket"], rep=r["rep"], reviews=len(revs), after=r["hidden_passed"], hidden=r["hidden_total"])
        if not revs or not r["pr"]:
            out.append(dict(row, before=None, note="no review stage" if not revs else "no PR"))
            continue
        start = ts(revs[0]["started_at"])
        commits = json.loads(subprocess.run(["gh", "api", f"repos/{r['repo']}/pulls/{r['pr']}/commits?per_page=100"],
                                            check=True, capture_output=True, text=True).stdout)
        before = [c["sha"] for c in commits if ts(c["commit"]["committer"]["date"]) <= start]
        if not before:
            out.append(dict(row, before=None, note="no commit before the first review"))
            continue
        sha = before[-1]
        m = re.search(r"\b([0-9a-f]{40})\b", (revs[0].get("summary") or "") + (revs[0].get("report") or ""))
        named = m.group(1) if m else None
        tag = f"C-before"
        g = subprocess.run(["bash", f"{X}/scripts/grade.sh", r["ticket"], tag, str(r["rep"]), sha, r["repo"]],
                           capture_output=True, text=True, env=dict(os.environ, GRADE_SET="main-review"))
        v = os.path.join(X, "results", "main-review", "runs", r["ticket"], tag, "codex", str(r["rep"]), "verify-summary.json")
        s = json.load(open(v)) if os.path.exists(v) else None
        b = sum(c == "pass" for c in s["cases"].values()) if s and s["mvn_exit"] == 0 else 0
        out.append(dict(row, before=b, before_sha=sha, review_named_sha=named, sha_matches=(named == sha) if named else None,
                        before_compiles=bool(s and s["mvn_exit"] == 0)))
        print(r["ticket"], r["rep"], f"before {b} after {r['hidden_passed']} / {r['hidden_total']}",
              "match" if named == sha else ("no named sha" if not named else f"MISMATCH named {named[:8]}"), flush=True)
    json.dump(out, open(os.path.join(MAIN, "review-effect.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
