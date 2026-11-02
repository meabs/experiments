"""Drives one run: a single Codex turn on one ticket, with one condition and one arm, then grades it.

  python3 -I run.py new <run> --task C1 --arm M --fault EXCL1
  python3 -I run.py go <run>        the agent's turn
  python3 -I run.py grade <run>

Runs live in $CG_WORK/<run>/ (default ~/code/benchmark/cg-work): ws/ (the repository the agent works in, a git
repository whose first commit is the starting state), codex-home/ (the session), events.jsonl (Codex's event stream),
final.md (the agent's messages), meta.json, grade.json, gate.json (the arm's own gate, run by the grader on the
final workspace with the gate files restored). Run IDs are anonymous; key.json in $CG_WORK maps them.
Adapted from 2026-11-broken-tools' run.py.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile, time

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(os.path.dirname(E), "2026-10-sec-authz", "app")
W = os.environ.get("CG_WORK", os.path.expanduser("~/code/benchmark/cg-work"))
WRAP = os.path.join(E, "setup", "codex-bwrap.sh")
MODEL, EFFORT = "gpt-5.6-luna", "medium"
TASKS, ARMS, FAULTS = ["C1", "C2", "L1X", "S2X"], ["C", "M"], ["F0", "EXCL", "EXCL1", "STALE"]
GATE_FILES = ["scripts/verify.sh", "tests/expected-tests.txt"]
GIT = ["git", "-c", "user.name=trial", "-c", "user.email=trial@example.com"]


def rdir(run):
    return os.path.join(W, run)


def meta(run):
    return json.load(open(os.path.join(rdir(run), "meta.json")))


def save_meta(run, m):
    json.dump(m, open(os.path.join(rdir(run), "meta.json"), "w"), indent=1)


def new(run, task, arm, fault):
    assert task in TASKS and arm in ARMS and fault in FAULTS
    assert not (fault == "STALE" and arm != "M"), "STALE is for the completeness arm only"
    d = rdir(run)
    if os.path.exists(d):
        sys.exit(f"{d} exists")
    ws = os.path.join(d, "ws")
    shutil.copytree(APP, ws, ignore=shutil.ignore_patterns("target"))
    shutil.copytree(os.path.join(E, "starter"), ws, dirs_exist_ok=True)
    shutil.copytree(os.path.join(E, "arms", arm), ws, dirs_exist_ok=True)
    if fault != "F0":
        shutil.copytree(os.path.join(E, "faults", fault), ws, dirs_exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(GIT + ["add", "-A"], cwd=ws, check=True)
    subprocess.run(GIT + ["commit", "-q", "-m", "accounts-service"], cwd=ws, check=True)
    save_meta(run, {"run": run, "task": task, "arm": arm, "fault": fault, "session": None,
                    "model": MODEL, "effort": EFFORT, "created": time.time()})
    print(d)


def go(run):
    m, d = meta(run), rdir(run)
    message = open(os.path.join(E, "tasks", m["task"], "prompt.md")).read().rstrip()
    cmd = ["bash", WRAP, "exec", "--skip-git-repo-check", "--json", "--model", MODEL, "-s", "danger-full-access",
           "-c", f'model_reasoning_effort="{EFFORT}"', "--enable", "multi_agent_v2", "-"]
    env = {"RUN_CODEX_HOME": os.path.join(d, "codex-home"), "PATH": "/usr/local/bin:/usr/bin:/bin",
           "HOME": os.path.expanduser("~")}
    t0 = time.time()
    with open(os.path.join(d, "events.jsonl"), "w") as out, open(os.path.join(d, "stderr.txt"), "w") as err:
        p = subprocess.Popen(cmd, cwd=os.path.join(d, "ws"), stdin=subprocess.PIPE, text=True, stdout=out,
                             stderr=err, env=env, start_new_session=True)
        p.stdin.write(message)
        p.stdin.close()
        stalled = watch(p, os.path.join(d, "events.jsonl"), t0)
    for line in open(os.path.join(d, "events.jsonl")):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "thread.started":
            m["session"] = e["thread_id"]
            break
    m.update({"exit": p.returncode, "seconds": round(time.time() - t0, 1), **({"stalled": stalled} if stalled else {})})
    save_meta(run, m)
    open(os.path.join(d, "final.md"), "w").write(agent_text(os.path.join(d, "events.jsonl")))
    subprocess.run(GIT + ["add", "-A"], cwd=os.path.join(d, "ws"))
    open(os.path.join(d, "ws.diff"), "w").write(
        subprocess.run(GIT + ["diff", "--cached", "HEAD", "--", ".", ":(exclude)target"], cwd=os.path.join(d, "ws"),
                       capture_output=True, text=True).stdout)
    print(run, m["task"], m["arm"], m["fault"], "exit", p.returncode, "seconds", m["seconds"], stalled or "")


STALL = 120  # seconds with no new event, in the turn or any subagent, while the agent sits in a `wait` call


def watch(p, jsonl, t0):
    """Waits for Codex to finish. Ends the turn if Codex hangs in a collaboration `wait` (the GRL and GVP amendment),
    or after 30 minutes in all. Returns why it ended the turn, or None."""
    while p.poll() is None:
        time.sleep(5)
        home = os.path.join(os.path.dirname(jsonl), "codex-home", "sessions")
        newest = max([os.path.getmtime(jsonl)] + [os.path.getmtime(f) for f in
                                                  glob.glob(os.path.join(home, "**", "*.jsonl"), recursive=True)])
        idle = time.time() - newest
        last = ""
        try:
            last = open(jsonl).read().rstrip().rsplit("\n", 1)[-1]
        except OSError:
            pass
        if idle > STALL and '"type":"item.started"' in last and '"tool":"wait"' in last:
            why = "wait"
        elif time.time() - t0 > 1800:
            why = "timeout"
        else:
            continue
        os.killpg(p.pid, 9)
        p.wait()
        return why
    return None


def agent_text(path):
    parts = []
    for line in open(path):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "item.completed" and e["item"].get("type") == "agent_message":
            parts.append(e["item"].get("text", ""))
    return "\n\n".join(parts) if parts else "(no message)"


def grade(run):
    m = meta(run)
    p = subprocess.run([sys.executable, "-I", os.path.join(E, "scripts", "grade.py"), m["task"],
                        os.path.join(rdir(run), "ws")], capture_output=True, text=True)
    open(os.path.join(rdir(run), "grade.json"), "w").write(p.stdout)
    r = json.loads(p.stdout)
    g = gate(run)
    print(run, m["task"], m["arm"], m["fault"], "correct", r["correct"], r["failed"][:2], "gate exit", g["exit"])


def gate(run):
    """Runs the arm's own gate on the final workspace, as the agent left it, with the gate files put back as they were
    at the start (so editing the list or the script doesn't change this result)."""
    m, d = meta(run), rdir(run)
    tmp = tempfile.mkdtemp(prefix="cg-gate-")
    try:
        ws = os.path.join(tmp, "ws")
        shutil.copytree(os.path.join(d, "ws"), ws, ignore=shutil.ignore_patterns(".git", "target"))
        for src in [os.path.join(E, "arms", m["arm"])] + ([os.path.join(E, "faults", m["fault"])] if m["fault"] != "F0" else []):
            for rel in GATE_FILES:
                if os.path.exists(os.path.join(src, rel)):
                    shutil.copy(os.path.join(src, rel), os.path.join(ws, rel))
        p = subprocess.run(["bash", "scripts/verify.sh"], cwd=ws, capture_output=True, text=True, timeout=900)
        out = {"exit": p.returncode, "lines": [l for l in p.stdout.splitlines() if re.match(r"(TESTS RUN|EXPECTED|MISSING|verify:)", l)]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    json.dump(out, open(os.path.join(d, "gate.json"), "w"), indent=1)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["new", "go", "grade"])
    ap.add_argument("run")
    ap.add_argument("--task")
    ap.add_argument("--arm")
    ap.add_argument("--fault")
    a = ap.parse_args()
    {"new": lambda: new(a.run, a.task, a.arm, a.fault), "go": lambda: go(a.run), "grade": lambda: grade(a.run)}[a.cmd]()
