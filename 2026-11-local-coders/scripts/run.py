"""Drives one run: a single local Codex turn on one task with one model, then grades it.

  python3 -I run.py new <run> --model qwen3-coder:30b --task g1_delete_item
  python3 -I run.py go <run>        the agent's turn (30-minute limit), with the APU power logged
  python3 -I run.py grade <run>

Set S (okf-local, arm okf): g1_delete_item, g2_add_voucher, g3_checkout_request, g4_orders_list. The workspace is the
storefront with okf-local's okf overlay; graded by okf-local's verify_g.sh (hidden test). The prompt is okf-local's, with
its suffix appended as AgentTrialRig did.
Set J (broken-tools, F0, arm A): C1, C2, L1X, S2X. The workspace is sec-authz's app with broken-tools' starter and arm A;
graded by broken-tools' grade.py.

Runs live in $LC_WORK/<run>/ (default ~/code/benchmark/lc-work): ws/, agent-homes/ (the Codex home, from the local
sandbox wrapper), events.jsonl, stderr.txt, final.md, ws.diff, power.csv, meta.json, grade.json.
"""
import argparse, json, os, shutil, signal, subprocess, sys, time, tomllib

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X = os.path.dirname(E)
OKF = os.path.join(X, "2026-10-okf-local")
BRK = os.path.join(X, "2026-11-broken-tools")
APP = os.path.join(X, "2026-10-sec-authz", "app")
FE = os.path.expanduser("~/code/benchmark/okf-local/fe")
FE_OVERLAY = os.path.expanduser("~/code/benchmark/okf-local/overlays/okf")
LOCAL = os.path.expanduser("~/code/benchmark/local-setup")
W = os.environ.get("LC_WORK", os.path.expanduser("~/code/benchmark/lc-work"))
MODELS_PILOT = ["qwen3-coder:30b", "qwen3.8:27b", "devstral-small-2:24b", "gpt-oss:20b", "flint:40b"]
# qwen3-coder dropped after its pilot (amendment log, 2026-11-02)
MODELS = ["qwen3.8:27b", "devstral-small-2:24b", "gpt-oss:20b", "flint:40b"]
SET_S = ["g1_delete_item", "g2_add_voucher", "g3_checkout_request", "g4_orders_list"]
SET_J = ["C1", "C2", "L1X", "S2X"]
TASKS = SET_S + SET_J
LIMIT, EFFORT = 1800, "medium"
# devstral has no thinking mode; Ollama rejects any effort but "none" (pilot, 2026-11-03)
EFFORT_BY_MODEL = {"devstral-small-2:24b": "none"}
GIT = ["git", "-c", "user.name=trial", "-c", "user.email=trial@example.com"]


def rdir(run):
    return os.path.join(W, run)


def meta(run):
    return json.load(open(os.path.join(rdir(run), "meta.json")))


def save_meta(run, m):
    json.dump(m, open(os.path.join(rdir(run), "meta.json"), "w"), indent=1)


def prompt(task):
    if task in SET_S:
        t = tomllib.load(open(os.path.join(OKF, "trial-okf.local.toml"), "rb"))
        q = next(q for q in t["questions"] if q["id"] == task)
        return q["prompt"] + " " + t["defaults"]["prompt_suffix"]
    return open(os.path.join(BRK, "tasks", task, "prompt.md")).read().rstrip()


def new(run, model, task):
    assert model in MODELS_PILOT and task in TASKS
    d = rdir(run)
    if os.path.exists(d):
        sys.exit(f"{d} exists")
    ws = os.path.join(d, "ws")
    if task in SET_S:
        shutil.copytree(FE, ws, ignore=shutil.ignore_patterns(".git", "node_modules"), symlinks=True)
        shutil.copytree(FE_OVERLAY, ws, dirs_exist_ok=True)
        if os.path.isdir(os.path.join(FE, "node_modules")):
            os.symlink(os.path.join(FE, "node_modules"), os.path.join(ws, "node_modules"))
    else:
        shutil.copytree(APP, ws, ignore=shutil.ignore_patterns("target"))
        shutil.copytree(os.path.join(BRK, "starter"), ws, dirs_exist_ok=True)
        shutil.copytree(os.path.join(BRK, "arms", "A"), ws, dirs_exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(GIT + ["add", "-A"], cwd=ws, check=True)
    subprocess.run(GIT + ["commit", "-q", "-m", "start"], cwd=ws, check=True)
    save_meta(run, {"run": run, "model": model, "task": task, "set": "S" if task in SET_S else "J",
                    "effort": EFFORT_BY_MODEL.get(model, EFFORT), "created": time.time()})
    print(d)


def go(run):
    m, d = meta(run), rdir(run)
    cmd = ["bash", os.path.join(LOCAL, "codex-bwrap.sh"), "exec", "-s", "danger-full-access", "--skip-git-repo-check",
           "--json", "--model", m["model"], "-c", f'model_reasoning_effort="{EFFORT_BY_MODEL.get(m["model"], EFFORT)}"', "-c", 'web_search="disabled"',
           prompt(m["task"])]
    env = {**os.environ, "TRIAL_OUT": d, "TRIAL_ID": run}
    power = subprocess.Popen(["bash", os.path.join(LOCAL, "powerlog.sh"), os.path.join(d, "power.csv")],
                             start_new_session=True)
    t0 = time.time()
    timed_out = False
    with open(os.path.join(d, "events.jsonl"), "w") as out, open(os.path.join(d, "stderr.txt"), "w") as err:
        p = subprocess.Popen(cmd, cwd=os.path.join(d, "ws"), stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                             env=env, start_new_session=True)
        try:
            p.wait(timeout=LIMIT)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            timed_out = True
    secs = round(time.time() - t0, 1)
    os.killpg(power.pid, signal.SIGTERM)
    m.update({"exit": p.returncode, "seconds": secs, "timed_out": timed_out, "started": t0})
    save_meta(run, m)
    open(os.path.join(d, "final.md"), "w").write(agent_text(os.path.join(d, "events.jsonl")))
    ws = os.path.join(d, "ws")
    subprocess.run(GIT + ["add", "-A"], cwd=ws)
    open(os.path.join(d, "ws.diff"), "w").write(subprocess.run(
        GIT + ["diff", "--cached", "HEAD", "--", ".", ":(exclude)target", ":(exclude)node_modules"], cwd=ws,
        capture_output=True, text=True).stdout)
    print(run, m["model"], m["task"], "exit", p.returncode, "seconds", secs, "TIMEOUT" if timed_out else "")


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
    m, d = meta(run), rdir(run)
    ws = os.path.join(d, "ws")
    if m["set"] == "S":
        env = {**os.environ, "TRIAL_DIR": ws, "OKF_EXP": OKF}
        p = subprocess.run(["bash", os.path.join(OKF, "scripts", "verify_g.sh"), m["task"]], env=env,
                           capture_output=True, text=True, timeout=600)
        r = {"correct": p.returncode == 0, "output": (p.stdout + p.stderr)[-1500:]}
    else:
        p = subprocess.run([sys.executable, "-I", os.path.join(BRK, "scripts", "grade.py"), m["task"], ws],
                           capture_output=True, text=True)
        r = json.loads(p.stdout)
    r["passed"] = bool(r["correct"]) and not m.get("timed_out")
    json.dump(r, open(os.path.join(d, "grade.json"), "w"), indent=1)
    print(run, m["model"], m["task"], "passed", r["passed"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["new", "go", "grade"])
    ap.add_argument("run")
    ap.add_argument("--model")
    ap.add_argument("--task")
    a = ap.parse_args()
    {"new": lambda: new(a.run, a.model, a.task), "go": lambda: go(a.run), "grade": lambda: grade(a.run)}[a.cmd]()
