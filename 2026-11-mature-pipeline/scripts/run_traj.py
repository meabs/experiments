"""One release trajectory: two agents (one per service) work in separate repositories from the same base, their changes are
merged, and the mature release pipeline (unit tests, CI estate smoke, mixed-version deployment rehearsal with rollback and fault
injection) runs in EVERY arm; a held release goes back to the agents for up to MAX_REPAIR repair rounds; then the release is executed
on the simulator and the independent oracle judges it. Arms: A independent; B plus awareness of the peer change; C plus awareness and
an executable release plan.

Usage: python3 -I scripts/run_traj.py <arm A|B|C> <scenario S0..S5> <rep> <out dir> [--ref safe|unsafe]
  --ref  skips the agents and applies the reference changes (free pipeline test).
Writes <out>/runs/<scenario>/<arm>/<rep>/{result.json, release.json, gate*.json, session-*.jsonl, *.patch, ...}
"""
import json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import tickets, trx  # noqa: E402

MAX_REPAIR = 2
PRICE = {"input": 0.20, "cached": 0.02, "output": 1.20}
ARM, SCEN, REP, OUT = sys.argv[1], sys.argv[2], sys.argv[3], os.path.abspath(sys.argv[4])
REF = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else None
R = os.path.join(OUT, "runs", SCEN, ARM, REP)
shutil.rmtree(R, ignore_errors=True)
os.makedirs(R)
SV = tickets.SERVICES[SCEN]
BASE_JARS = os.path.join(ROOT, "build", "base")
t0 = time.time()


def prep(svc):
    W = os.path.join(R, "work", svc)
    shutil.copytree(os.path.join(ROOT, "estate", svc), os.path.join(W, svc), ignore=shutil.ignore_patterns("target"))
    shutil.copytree(os.path.join(ROOT, "estate", "contracts"), os.path.join(W, "contracts"))
    title, body = tickets.T[SCEN][svc]
    open(os.path.join(W, "TICKET.md"), "w").write(f"# {title}\n\n{body}\n")
    extra = ""
    prompt = tickets.BASE_PROMPT
    if ARM in ("B", "C"):
        other = [s for s in SV if s != svc][0]
        os.makedirs(os.path.join(W, "release"), exist_ok=True)
        for s in os.listdir(os.path.join(ROOT, "estate")):
            if s in tickets.SERVICES["S0"] + ["ledger", "notifier"] and os.path.isdir(os.path.join(ROOT, "estate", s)) and s != svc:
                shutil.copytree(os.path.join(ROOT, "estate", s), os.path.join(W, "peers", s), ignore=shutil.ignore_patterns("target"))
        txt = tickets.COORD if ARM == "C" else tickets.AWARE
        if ARM == "B":
            shutil.rmtree(os.path.join(W, "release"))
        extra = " and `release/`" if ARM == "C" else ""
        prompt = prompt + txt.replace("{other}", other).replace("{other_title}", tickets.T[SCEN][other][0])
    open(os.path.join(R, f"prompt-{svc}.txt"), "w").write(prompt.replace("{svc}", svc).replace("{extra_dirs}", extra))
    return W


def run_agents(tag, extra_by_svc=None):
    procs = []
    for svc in SV:
        pf = os.path.join(R, f"prompt-{svc}.txt")
        if extra_by_svc:
            pf = os.path.join(R, f"prompt-{svc}-{tag}.txt")
            open(pf, "w").write(open(os.path.join(R, f"prompt-{svc}.txt")).read() + extra_by_svc[svc])
        # a repair run starts from the work folder as the first run left it, with the report appended
        sess = os.path.join(R, f"session-{svc}-{tag}.jsonl")
        procs.append(subprocess.Popen(["bash", os.path.join(HERE, "run_agent.sh"), os.path.join(R, "work", svc), R, f"{svc}-{tag}", pf, sess]))
    for p in procs:
        p.wait()


def auth_failed():
    """True if any agent session died of a login error: such a trajectory is not a result, so it is not written and a rerun redoes it."""
    for f in os.listdir(R):
        if f.startswith("session-") and (f.endswith(".jsonl") or f.endswith(".jsonl.err")):
            t = open(os.path.join(R, f), errors="replace").read()
            if "refresh_token_reused" in t or "unauthorized (401)" in t or "401 Unauthorized" in t:
                return True
    return False


def tokens(path):
    u = {"input": 0, "cached": 0, "output": 0}
    if os.path.exists(path):
        for l in open(path, errors="replace"):
            try:
                j = json.loads(l)
            except ValueError:
                continue
            if j.get("type") == "turn.completed":
                x = j.get("usage", {})
                u["input"] += x.get("input_tokens", 0); u["cached"] += x.get("cached_input_tokens", 0); u["output"] += x.get("output_tokens", 0)
    return u


def apply_ref():
    vdir = os.path.join(ROOT, "refs", SCEN, REF)
    for svc in SV:
        src = os.path.join(vdir, svc)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(R, "work", svc, svc), dirs_exist_ok=True)
    plan = os.path.join(vdir, "plan.txt")
    return plan if os.path.exists(plan) else None


def constraints():
    c = {}
    for svc in SV:
        p = os.path.join(R, "work", svc, "release", "plan.json")
        if os.path.exists(p):
            try:
                d = json.load(open(p))
                if isinstance(d, dict):
                    c[svc] = {"deploy_after": [x for x in d.get("deploy_after", []) if isinstance(x, str)],
                              "atomic_with": [x for x in d.get("atomic_with", []) if isinstance(x, str)],
                              "drain_before": bool(d.get("drain_before"))}
            except Exception:
                pass
    return c


def evaluate(tag, ref_plan=None):
    cand = os.path.join(R, f"cand-{tag}")
    shutil.rmtree(cand, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "estate"), cand, ignore=shutil.ignore_patterns("target", "_common"))
    for svc in SV:
        shutil.rmtree(os.path.join(cand, svc, "src"))
        shutil.copytree(os.path.join(R, "work", svc, svc, "src"), os.path.join(cand, svc, "src"))
    jars = os.path.join(R, f"jars-{tag}")
    unit = trx.build(cand, jars)
    ev = {"unit": unit, "ci": [], "constraints": {}, "plan": None}
    for svc in SV:
        for kind in ("src",):
            pass
    if unit == "unit ok":
        ci = trx.sim("ci", SCEN, jars, jars, SV, None, os.path.join(R, f"ci-{tag}.json"))
        ev["ci"] = [f"{v['inv']}: {v['detail']}" for v in ci["violations"]]
    cons = constraints() if ARM == "C" else {}
    ev["constraints"] = cons
    plan = ref_plan
    if plan is None and cons:
        text = trx.merge_plans(cons, SV)
        if text:
            plan = os.path.join(R, f"plan-{tag}.txt")
            open(plan, "w").write(text)
    ev["plan"] = open(plan).read() if plan else None
    ev["plan_path"] = plan
    ev["jars"] = jars
    ev["ci_green"] = unit == "unit ok" and not ev["ci"]
    if unit == "unit ok":
        g = trx.sim("gate", SCEN, BASE_JARS, jars, SV, plan, os.path.join(R, f"gate-{tag}.json"))
        ev["gate"] = g["verdict"]
        ev["gate_violations"] = [(r["fault"], v["inv"], v["detail"], v["at"]) for r in g["runs"] for v in r["violations"]]
    else:
        ev["gate"] = None
        ev["gate_violations"] = []
    ev["held"] = (not ev["ci_green"]) or ev["gate"] == "reject"
    ev["oracle"] = oracle(ev, tag) if unit == "unit ok" else None
    return ev


def verdict(rel):
    d = rel["delivered"]
    delivered = bool(d) and all(d.values()) and not rel["aborted"]
    return {"delivered": delivered, "n_violations": len(rel["violations"]), "recovered": rel["recovered"],
            "safe": delivered and not rel["violations"] and rel["recovered"] is not False,
            "violations": [{"inv": v["inv"], "detail": v["detail"], "at": v["at"]} for v in rel["violations"]]}


def oracle(ev, tag):
    """The independent oracle's verdict on a candidate released as its plan says (and, when it has a plan, in the default order too).
    Run for every candidate, held or not, so held candidates can be judged afterwards (unnecessary blocking) and the effect of the plan separated from the code."""
    rel = trx.sim("release", SCEN, BASE_JARS, ev["jars"], SV, ev["plan_path"], os.path.join(R, f"release-{tag}.json"))
    o = verdict(rel)
    if ev["plan_path"]:
        o["default_order"] = verdict(trx.sim("release", SCEN, BASE_JARS, ev["jars"], SV, None, os.path.join(R, f"release-default-{tag}.json")))
    else:
        o["default_order"] = {k: o[k] for k in ("delivered", "safe", "n_violations")}
    return o


def report_for(svc, ev, gate):
    lines = []
    if ev["unit"] != "unit ok":
        log = os.path.join(ev["jars"], f"{svc}.build.log")
        tail = open(log, errors="replace").read().splitlines()[-40:] if os.path.exists(log) else []
        bad = ev["unit"]
        lines.append(f"Unit tests / build: {bad}\n" + "\n".join(tail))
    lines += ["CI estate check: " + x for x in ev["ci"]]
    if gate and ev["gate"] == "reject":
        lines.append("Deployment rehearsal: REJECT. The pipeline rolls the release out on a staging estate one instance at a time under test traffic, "
                     "injects a failed rollout with rollback, and checks the estate for consistency. Findings (rule, detail, when):")
        seen = set()
        for f, inv, d, at in ev["gate_violations"]:
            k = (inv, d)
            if k in seen:
                continue
            seen.add(k)
            lines.append(f"- {inv}: {d} (at {at}; failed rollout of {f})")
    return "\n".join(lines)


# ------------------------------------------------------------------ main flow
for svc in SV:
    prep(svc)
ref_plan = None
if REF:
    ref_plan = apply_ref()
else:
    run_agents("a")
    if auth_failed():
        shutil.rmtree(os.path.join(R, "agent-homes"), ignore_errors=True); shutil.rmtree(os.path.join(R, "work"), ignore_errors=True)
        print("AUTH FAILURE, trajectory not recorded", ARM, SCEN, REP); sys.exit(3)
rounds = [evaluate("0", ref_plan)]
while rounds[-1]["held"] and not REF and len(rounds) <= MAX_REPAIR:
    ev0 = rounds[-1]
    extra = {}
    for svc in SV:
        rep = report_for(svc, ev0, True)
        extra[svc] = (tickets.GATE_REPORT if ev0["ci_green"] else tickets.CI_REPORT).replace("{report}", rep).replace("{svc}", svc)
    run_agents(f"repair{len(rounds)}", extra)
    if auth_failed():
        shutil.rmtree(os.path.join(R, "agent-homes"), ignore_errors=True); shutil.rmtree(os.path.join(R, "work"), ignore_errors=True)
        print("AUTH FAILURE in repair, trajectory not recorded", ARM, SCEN, REP); sys.exit(3)
    rounds.append(evaluate(str(len(rounds))))
ev = rounds[-1]
ev0 = rounds[0]
repairs = len(rounds) - 1
released = not ev["held"]
o_final = ev["oracle"]
o_first = ev0["oracle"]
res = {"scenario": SCEN, "arm": ARM, "rep": REP, "ref": REF, "repairs": repairs, "released": released,
       "held_final": ev["held"],
       "pipeline_pass_first": not ev0["held"],
       "safe_first": bool(not ev0["held"] and o_first and o_first["safe"]),
       "oracle_first_candidate_safe": bool(o_first and o_first["safe"]),
       "rounds": [{"unit": e["unit"], "ci_green": e["ci_green"], "gate": e["gate"], "held": e["held"],
                   "gate_rules": sorted({v[1] for v in e["gate_violations"]}),
                   "oracle_safe": bool(e["oracle"] and e["oracle"]["safe"]),
                   "oracle_delivered": bool(e["oracle"] and e["oracle"]["delivered"]),
                   "oracle_violations": (e["oracle"] or {}).get("n_violations"),
                   "oracle_default_order_safe": bool(e["oracle"] and e["oracle"]["default_order"]["safe"])} for e in rounds],
       # unnecessary blocking: rounds the pipeline held although the oracle judged the candidate safe
       "false_holds": sum(1 for e in rounds if e["held"] and e["oracle"] and e["oracle"]["safe"]),
       "constraints": ev["constraints"], "plan": ev["plan"]}
if released and o_final:
    res.update({"violations": o_final["violations"], "n_violations": o_final["n_violations"], "recovered": o_final["recovered"],
                "delivered": o_final["delivered"], "safe": o_final["safe"],
                "safe_default_order": o_final["default_order"]["safe"],
                "unsafe_green": (not ev["held"]) and not o_final["safe"]})
else:
    res.update({"violations": [], "n_violations": 0, "recovered": None, "delivered": False, "safe": False, "safe_default_order": False,
                "unsafe_green": False})
tot = {"input": 0, "cached": 0, "output": 0}
for f in os.listdir(R):
    if f.startswith("session-") and f.endswith(".jsonl"):
        u = tokens(os.path.join(R, f))
        for k in tot:
            tot[k] += u[k]
res["tokens"] = tot
res["cost_usd"] = ((tot["input"] - tot["cached"]) * PRICE["input"] + tot["cached"] * PRICE["cached"] + tot["output"] * PRICE["output"]) / 1e6
res["seconds"] = round(time.time() - t0)
if released and o_final:
    shutil.copy(os.path.join(R, f"release-{len(rounds) - 1}.json"), os.path.join(R, "release.json"))
for svc in SV:
    p = subprocess.run(["diff", "-ruN", os.path.join(ROOT, "estate", svc, "src"), os.path.join(R, "work", svc, svc, "src")], capture_output=True, text=True)
    open(os.path.join(R, f"agent-{svc}.patch"), "w").write(p.stdout)
    for f in ("release/plan.json", "release/RELEASE.md"):
        s = os.path.join(R, "work", svc, f)
        if os.path.exists(s):
            shutil.copy(s, os.path.join(R, f"{svc}-{os.path.basename(f)}"))
json.dump(res, open(os.path.join(R, "result.json"), "w"), indent=1)
for d in os.listdir(R):
    if d.startswith(("cand-", "jars-")) or d in ("work",):
        shutil.rmtree(os.path.join(R, d), ignore_errors=True)
shutil.rmtree(os.path.join(R, "agent-homes"), ignore_errors=True)
print(json.dumps({k: res[k] for k in ("scenario", "arm", "rep", "released", "delivered", "safe", "safe_first", "repairs", "false_holds", "cost_usd", "seconds")}))
