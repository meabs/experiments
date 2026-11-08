"""Runs arm B (Machinist `single`) or C (Machinist `factory`, stock) runs, one at a time, each in its own repository.

For each run TICKET:ARM:REP:
  1. run-repo.sh create asf-run-NNN (fresh private repo holding the single-commit base, on the App installation,
     registered with Machinist), then detach the previous run's repository (GitHub refuses an empty installation);
  2. submit the job with the same ticket text arm A gets (make_trial_a.ticket_text);
  3. wait for it to end. A spec waiting for approval is approved at once, as a hands-off user would, and logged.
     A job still running after CAP_S is cancelled;
  4. grade the head of the run's PR with grade.sh (no PR: score 0), collect the Codex evidence (evidence.py), and
     append one line to results/<SET>/bc-runs.jsonl.

Usage: python3 -I run_bc.py SET TICKET:ARM:REP [...]      (ARM is B or C)
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

X = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(X, "scripts"))
from make_trial_a import ticket_text  # noqa: E402

API = "http://127.0.0.1:7331"
TOKEN = open(os.path.expanduser("~/.machinist/server/worker.token")).read().strip()
RECIPE = {"B": "single", "C": "factory"}
WAITING = {"queued", "running", "awaiting_runner", "awaiting_dispatch"}
CAP_S = 3 * 3600
POLL_S = 20


def api(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read() or b"null")


def job(jid):
    for j in api("GET", "/api/v1/status")["jobs"]:
        if j["id"] == jid:
            return j
    raise KeyError(jid)


def next_run_number(out):
    f = os.path.join(X, "results", "run-counter")  # one sequence across all sets
    n = int(open(f).read()) if os.path.exists(f) else 1  # asf-run-000 was the smoke
    open(f, "w").write(str(n + 1))
    return n


def sh(*args, **kw):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kw).stdout


def log(out, msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {msg}"
    print(line, flush=True)
    open(os.path.join(out, "bc-events.log"), "a").write(line + "\n")


def run_one(set_, out, ticket, arm, rep, previous):
    name = f"asf-run-{next_run_number(out):03d}"
    repo = f"meabs/{name}"
    log(out, f"{ticket}/{arm}/{rep}: {sh('bash', f'{X}/scripts/run-repo.sh', 'create', name).strip()}")
    if previous:
        log(out, sh("bash", f"{X}/scripts/run-repo.sh", "detach", previous.split("/")[1]).strip())
    jid = api("POST", "/api/v1/jobs", {"recipe": RECIPE[arm], "repository": repo, "title": ticket,
                                       "prompt": ticket_text(ticket),
                                       "client_request_id": f"asf-{set_}-{arm}-{ticket}-{rep}"})["id"]
    t0 = time.time()
    approvals, cancelled = [], False
    log(out, f"{ticket}/{arm}/{rep}: job {jid} in {repo}")
    while True:
        j = job(jid)
        if j["state"] == "awaiting_approval":
            run_id = j["runs"][-1]["id"]
            api("POST", f"/api/v1/jobs/{jid}/approve", {"run_id": run_id})
            approvals.append({"run_id": run_id, "at_s": round(time.time() - t0)})
            log(out, f"{ticket}/{arm}/{rep}: approved spec (run {run_id})")
        elif j["state"] not in WAITING:
            break
        elif time.time() - t0 > CAP_S and not cancelled:
            api("POST", f"/api/v1/jobs/{jid}/cancel", {"run_id": j["runs"][-1]["id"]})
            cancelled = True
            log(out, f"{ticket}/{arm}/{rep}: cancelled at the {CAP_S} s cap")
        time.sleep(POLL_S)
    wall = round(time.time() - t0)
    rd = os.path.join(out, "runs", ticket, arm, "codex", str(rep))
    os.makedirs(rd, exist_ok=True)
    json.dump(j, open(os.path.join(rd, "machinist-job.json"), "w"), indent=1)
    pr_url = ((j.get("workflow") or {}).get("factory") or {}).get("pr_url") or ""
    pr = pr_url.rsplit("/", 1)[-1] if pr_url.startswith(f"https://github.com/{repo}/pull/") else ""
    pr_source = "machinist" if pr else ""
    if not pr:
        # Machinist records no PR when it rejects a stage's reply, though the agent may have opened one. The run's
        # repository is fresh, so any PR in it is this run's (amendment-log item 12).
        prs = json.loads(sh("gh", "pr", "list", "-R", repo, "--state", "all", "--json", "number"))
        if prs:
            pr, pr_source = str(min(p["number"] for p in prs)), f"github ({len(prs)} PR)"
    grade = None
    if pr:
        g = subprocess.run(["bash", f"{X}/scripts/grade.sh", ticket, arm, str(rep), pr, repo], text=True,
                           capture_output=True, env=dict(os.environ, GRADE_SET=set_))
        open(os.path.join(rd, "grade.log"), "w").write(g.stdout + g.stderr)
        p = os.path.join(rd, "verify-summary.json")
        grade = json.load(open(p)) if os.path.exists(p) else None
    ev = json.loads(sh("python3", "-I", f"{X}/scripts/evidence.py", jid, os.path.join(rd, "evidence.json")))
    cases = (grade or {}).get("cases", {})
    row = {"ticket": ticket, "arm": arm, "rep": rep, "repo": repo, "job": jid, "state": j["state"],
           "stages": [r.get("command") for r in j.get("runs", [])], "pr": pr, "pr_source": pr_source,
           "wall_s": wall, "approvals": approvals, "cancelled_at_cap": cancelled,
           "hidden_passed": sum(v == "pass" for v in cases.values()),
           "hidden_total": (grade or {}).get("hidden_expected") or len(cases) or None,
           "compiles": (grade or {}).get("mvn_exit") == 0 if grade else None,
           "cost_usd": ev["cost_usd"], "tokens": ev["tokens"], "luna_only": ev["luna_only"], "leaks": len(ev["leaks"])}
    open(os.path.join(out, "bc-runs.jsonl"), "a").write(json.dumps(row) + "\n")
    log(out, f"{ticket}/{arm}/{rep}: {j['state']}, PR {pr or '-'}, hidden {row['hidden_passed']}/{row['hidden_total']}, "
             f"${ev['cost_usd']:.3f}, {wall} s, luna_only={ev['luna_only']}, leaks={len(ev['leaks'])}")
    return repo


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    set_ = sys.argv[1]
    out = os.path.join(X, "results", set_)
    os.makedirs(out, exist_ok=True)
    prev_file = os.path.join(X, "results", "attached-repo")  # the one repository on the installation now
    previous = open(prev_file).read().strip() if os.path.exists(prev_file) else "meabs/asf-run-000"
    for spec in sys.argv[2:]:
        ticket, arm, rep = spec.split(":")
        assert arm in RECIPE, arm
        previous = run_one(set_, out, ticket, arm, int(rep), previous)
        open(prev_file, "w").write(previous)


if __name__ == "__main__":
    main()
