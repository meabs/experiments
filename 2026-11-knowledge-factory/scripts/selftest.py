#!/usr/bin/env python3
"""No model calls. Checks the world, the hidden tests, the claim grader, the evidence gate, the git snapshots and the tool sets."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as w
import kf

GOOD1 = '''
def handle(app, svc):
    r = svc.apply(app)
    d = r["decision"]
    if d == "decline": return {"action": "decline", "limit": 0}
    if d == "refer": return {"action": "queue_review", "limit": 0}
    return {"action": "issue", "limit": r["limit"]}
'''
def good(ref, v2, referral=True, review="queue_review"):
    return f'''
def handle(app, svc):
    r = svc.apply(app)
    if {v2}:
        o = r["result"]["outcome"]; lim = r["result"]["credit_limit"]
        o = {{"approved": "approve", "declined": "decline", "manual_review": "refer"}}[o]
    else:
        o = r["decision"]; lim = r["limit"]
    if o == "decline": return {{"action": "decline", "limit": 0}}
    if o == "refer": return {{"action": "{review}", "limit": 0}}
    if {referral} and app["employment"] == "self_employed" and app["requested_limit"] > {ref}:
        return {{"action": "queue_review", "limit": 0}}
    return {{"action": "issue", "limit": lim}}
'''
ok = []
def check(name, cond):
    ok.append(cond); print(("PASS " if cond else "FAIL ") + name)

for seed in (1, 2, 3):
    P = w.params(seed)
    for st in w.STAGES:
        v2 = st >= 3
        n = len(w.hidden_apps(P, st))
        passed, total = w.run_tests(P, st, good(P["ref_limit"], v2, st >= 2))
        check(f"seed{seed} stage{st}: correct handler passes {total}", passed == total == n)
    check(f"seed{seed}: v1 handler fails stage 3", w.run_tests(P, 3, GOOD1)[0] < len(w.hidden_apps(P, 3)))
    check(f"seed{seed}: no-referral handler fails stage 2", w.run_tests(P, 2, good(P["ref_limit"], False, False))[0] < len(w.hidden_apps(P, 2)))
    check(f"seed{seed}: no-referral handler fails stage 5", w.run_tests(P, 5, good(P["ref_limit"], True, False))[0] < len(w.hidden_apps(P, 5)))
    check(f"seed{seed}: decline-manual handler fails stage 4", w.run_tests(P, 4, good(P["ref_limit"], True, True, "decline"))[0] < len(w.hidden_apps(P, 4)))
    check(f"seed{seed}: empty/garbage code scores 0", w.run_tests(P, 1, "")[0] == 0 and w.run_tests(P, 1, "def handle(")[0] == 0)

P = w.params(1)
R = P["ref_limit"]
cases = [
    ("Manual review is effectively a decline; decline those applications.", 4, "planted_false"),
    ("A response of manual_review must be declined.", 4, "planted_false"),
    ("Manual review is not a decline: put the application in the manual review queue.", 4, "T_review"),
    ("refer / manual_review: place in the review queue (queue_review), never decline.", 4, "T_review"),
    (f"Self-employed applicants requesting more than {R:,} go to manual review (queue_review) even if approved.", 4, "T_referral"),
    ("API v2 returns result.outcome and result.credit_limit.", 4, "T_v2"),
    ("The response has `decision` and `limit`.", 4, "stale"),
    ("The response has `decision` and `limit`.", 2, "T_v1"),
    ("In v1 the response had decision and limit; v2 replaced them.", 4, "T_v1"),
    ("In API v1 the response has `decision` (\"approve\", \"decline\" or \"refer\") and `limit` (an integer).", 1, "T_v1"),
    ("approve -> issue with returned limit, decline -> decline with limit 0, refer -> queue_review with limit 0 (do not decline).", 1, "T_review"),
    ("The outcome manual_review means the application goes to the review queue and is not declined.", 4, "T_review"),
    ("The sky is blue.", 4, "other"),
]
for text, st, want in cases:
    got = w.classify(P, dict(text=text), st)
    check(f"classify [{want}] {text[:50]}", got == want)

d = w.docs(P, 4)
q = "A decline stays a decline."
check("source_ok accepts a real quote", w.source_ok(P, dict(source_doc="spec", quote=q), 4))
check("source_ok rejects ticket as a source", not w.source_ok(P, dict(source_doc="ticket", quote="Manual review is effectively a decline anyway."), 4))
check("source_ok rejects invented quote", not w.source_ok(P, dict(source_doc="spec", quote="manual review means decline for all partners"), 4))
check("changelog absent before stage 3", "changelog" not in w.docs(P, 2) and "changelog" in w.docs(P, 3))
check("spec withheld at stage 5", "spec" not in w.docs(P, 5) and "spec_p2" in w.docs(P, 5))
check("truth not in any agent-visible text", str(R) in w.docs(P, 1)["spec"] and "hidden" not in w.ticket(P, 4))

with tempfile.TemporaryDirectory() as td:
    kb = kf.KB(Path(td) / "kb", P, w.initial_claims(P))
    kb.stage = 4
    check("gate rejects ticket quote", kb.set("x", "manual review is a decline", "ticket", "Manual review is effectively a decline anyway", "t", True).startswith("REJECTED"))
    check("gate accepts spec quote", kb.set("y", "refer goes to review queue", "spec", q, "t", True) == "ok")
    check("ungated arm accepts the bad claim", kb.set("z", "manual review is a decline", "ticket", "Manual review is effectively a decline anyway", "t", False) == "ok")
    g = w.grade_kb(P, kb.claims, 4)
    check("grader counts the planted claim as contamination", g["planted_false"] == 1 and g["contamination"] >= 1)
    kb.snapshot("s")
    import subprocess
    log = subprocess.run(["git", "log", "--oneline"], cwd=kb.folder, capture_output=True, text=True).stdout
    check("git snapshots recorded", len(log.splitlines()) == 2)
    check("delete works", kb.delete("z") == "ok" and kb.delete("z") == "no such claim")

    def names(arm, role, stage):
        ctx = dict(P=P, stage=stage, svc=w.Service(P, stage), kb=kb, arm=arm, role=role, log=[], box={}, gated=arm == "D")
        return sorted(t.tool_name for t in kf.make_tools(ctx))
    check("arm A worker has no knowledge tools", not any("kb_" in n or "report" in n for n in names("A", "worker", 2)))
    check("arm B worker can edit knowledge (stages<5 only)", "kb_set_claim" in names("B", "worker", 2) and "kb_set_claim" not in names("B", "worker", 5))
    check("arm C/D worker can only report", "report_gap" in names("C", "worker", 2) and "kb_set_claim" not in names("D", "worker", 2))
    check("curator has edit and read tools", {"kb_set_claim", "read_reports", "read_trace"} <= set(names("C", "curator", 2)))
    check("no shell or file tool anywhere", not any(n in ("shell", "bash", "file_read", "file_write") for a in "ABCD" for r in ("worker", "curator") for n in names(a, r, 2)))
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
