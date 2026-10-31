"""Drives one run: a Codex session that may span several turns, with the developer's replies in between.

  python3 -I run.py new <run> --task S1 --arm G
  python3 -I run.py turn <run> [--message-file FILE]   first turn: the arm's opening message; later: the developer's reply
  python3 -I run.py auto <run>                         T runs: the single turn
  python3 -I run.py grade <run>

Runs live in $GVP_WORK/<run>/ (default ~/code/benchmark/gvp-work): ws/ (the repository the agent works in),
codex-home/ (the session), turns/NN.{dev,agent}.md, turns/NN.jsonl (Codex's event stream), meta.json, grade.json.
Arms: T ticket only; G grilling (the skill); S a structured prompt (list the open decisions, then wait); K a targeted
interview (at most three questions, then wait). Adapted from 2026-10-grilling's run.py.
"""
import argparse, glob, json, os, re, shutil, signal, subprocess, sys, time

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(os.path.dirname(E), "2026-10-sec-authz", "app")
W = os.environ.get("GVP_WORK", os.path.expanduser("~/code/benchmark/gvp-work"))
WRAP = os.path.join(E, "setup", "codex-bwrap.sh")
MODEL, EFFORT = "gpt-5.6-luna", "medium"
SKILLS = {"T": [], "G": ["grilling"], "S": [], "K": []}
OPENERS = {
    "T": "",
    "G": "Grill me on this before you build it.",
    "S": "Before writing any code, list every decision this ticket leaves open that you can't settle from the code, each "
         "with your recommended answer. Then stop and wait for my reply.",
    "K": "Before writing any code, ask me at most three questions: the ones whose answers would change the code most. "
         "Then stop and wait for my reply.",
}
MAX_TURNS = 12   # the developer caps the interview at 6 rounds; this is a safety stop
CAP = "That's enough questions, go with your recommendations."
GIT = ["git", "-c", "user.name=trial", "-c", "user.email=trial@example.com"]


def rdir(run):
    return os.path.join(W, run)


def meta(run):
    return json.load(open(os.path.join(rdir(run), "meta.json")))


def save_meta(run, m):
    json.dump(m, open(os.path.join(rdir(run), "meta.json"), "w"), indent=1)


def new(run, task, arm):
    d = rdir(run)
    if os.path.exists(d):
        sys.exit(f"{d} exists")
    ws = os.path.join(d, "ws")
    shutil.copytree(APP, ws, ignore=shutil.ignore_patterns("target"))
    shutil.copytree(os.path.join(E, "starter"), ws, dirs_exist_ok=True)
    shutil.copy(os.path.join(E, "arms", "AGENTS.md"), os.path.join(ws, "AGENTS.md"))
    for s in SKILLS[arm]:
        shutil.copytree(os.path.join(E, "arms", "skills", s), os.path.join(ws, ".agents", "skills", s))
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(GIT + ["add", "-A"], cwd=ws, check=True)
    subprocess.run(GIT + ["commit", "-q", "-m", "accounts-service"], cwd=ws, check=True)
    os.makedirs(os.path.join(d, "turns"))
    save_meta(run, {"run": run, "task": task, "arm": arm, "session": None,
                    "turns": 0, "model": MODEL, "effort": EFFORT, "created": time.time()})
    print(d)


def opening(m):
    text = open(os.path.join(E, "tasks", m["task"], "prompt.md")).read().rstrip()
    return text + ("\n\n" + OPENERS[m["arm"]] if OPENERS[m["arm"]] else "")


def turn(run, message=None):
    m, d = meta(run), rdir(run)
    n = m["turns"] + 1
    if n == 1:
        message = opening(m)
    elif message is None:
        sys.exit("later turns need the developer's message")
    open(os.path.join(d, "turns", f"{n:02d}.dev.md"), "w").write(message)
    last = os.path.join(d, "turns", f"{n:02d}.agent.md")
    # `exec resume` takes no -s, so the sandbox mode is set through config on every turn (the same setting).
    common = ["--skip-git-repo-check", "--json", "--model", MODEL, "-c", 'sandbox_mode="danger-full-access"',
              "-c", f'model_reasoning_effort="{EFFORT}"', "--enable", "multi_agent_v2"]
    if n == 1:
        cmd = ["bash", WRAP, "exec"] + common + ["-"]
    else:
        cmd = ["bash", WRAP, "exec", "resume"] + common + [m["session"], "-"]
    env = {"RUN_CODEX_HOME": os.path.join(d, "codex-home"), "PATH": "/usr/local/bin:/usr/bin:/bin",
           "HOME": os.path.expanduser("~")}
    t0 = time.time()
    with open(os.path.join(d, "turns", f"{n:02d}.jsonl"), "w") as out, \
            open(os.path.join(d, "turns", f"{n:02d}.stderr"), "w") as err:
        p = subprocess.Popen(cmd, cwd=os.path.join(d, "ws"), stdin=subprocess.PIPE, text=True, stdout=out,
                             stderr=err, env=env, start_new_session=True)
        p.stdin.write(message)
        p.stdin.close()
        stalled = watch(p, os.path.join(d, "turns", f"{n:02d}.jsonl"), t0)
    if m["session"] is None:
        for line in open(os.path.join(d, "turns", f"{n:02d}.jsonl")):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "thread.started":
                m["session"] = e["thread_id"]
                break
    m["turns"] = n
    m.setdefault("turn_log", []).append({"n": n, "exit": p.returncode, "seconds": round(time.time() - t0, 1),
                                         **({"stalled": stalled} if stalled else {})})
    save_meta(run, m)
    reply = agent_text(os.path.join(d, "turns", f"{n:02d}.jsonl"))
    open(last, "w").write(reply)
    return reply, p.returncode


STALL = 120  # seconds with no new event, in the turn or any subagent, while the agent sits in a `wait` call


def watch(p, jsonl, t0):
    """Waits for Codex to finish. Ends the turn if Codex hangs in a collaboration `wait` (amendment, 2026-10-31: the
    agent sometimes calls wait_agent with a one-hour timeout after posting its questions, or misses a finished
    subagent), or after 30 minutes in all. Returns why it ended the turn, or None."""
    while p.poll() is None:
        time.sleep(5)
        home = os.path.join(os.path.dirname(os.path.dirname(jsonl)), "codex-home", "sessions")
        newest = max([os.path.getmtime(jsonl)] + [os.path.getmtime(f) for f in
                                                  glob.glob(os.path.join(home, "**", "*.jsonl"), recursive=True)])
        idle = time.time() - newest   # subagents write to their own session files
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
    """Everything the agent said to the developer in one turn: all its messages, in order (a round of questions can
    come before a closing line)."""
    parts = []
    for line in open(path):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "item.completed" and e["item"].get("type") == "agent_message":
            parts.append(e["item"].get("text", ""))
    return "\n\n".join(parts) if parts else "(no message)"


def changed_main(run):
    p = subprocess.run(["git", "status", "--porcelain", "--", "src/main"], cwd=os.path.join(rdir(run), "ws"),
                       capture_output=True, text=True)
    return bool(p.stdout.strip())


def asking(text):
    """The agent's message is waiting for the developer (questions or a request to confirm)."""
    t = text.strip()
    return "❓" in t or bool(re.search(r"\*\*Q\d+\*\*", t)) or t.endswith("?") or \
        bool(re.search(r"(shall I|should I|do you want|confirm|go ahead|proceed)[^.\n]*\?", t, re.I))


def auto(run):
    if meta(run)["arm"] != "T":
        sys.exit("auto is for ticket-only runs; the interview arms go through relay.py")
    turn(run)


def grade(run):
    m = meta(run)
    task = m["task"]
    p = subprocess.run([sys.executable, "-I", os.path.join(E, "scripts", "grade.py"), task, os.path.join(rdir(run), "ws")],
                       capture_output=True, text=True)
    open(os.path.join(rdir(run), "grade.json"), "w").write(p.stdout)
    r = json.loads(p.stdout)
    print(run, task, "ticket_pass", r["ticket_pass"], "reqs", r["reqs"], "met", r["met"], "/", r["possible"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["new", "turn", "auto", "grade"])
    ap.add_argument("run")
    ap.add_argument("--task")
    ap.add_argument("--arm")
    ap.add_argument("--message-file")
    a = ap.parse_args()
    if a.cmd == "new":
        new(a.run, a.task, a.arm)
    elif a.cmd == "turn":
        msg = open(a.message_file).read() if a.message_file else None
        reply, code = turn(a.run, msg)
        print(reply)
        print(f"\n[turn {meta(a.run)['turns']} exit {code}; main code changed: {changed_main(a.run)}]")
    elif a.cmd == "auto":
        auto(a.run)
    else:
        grade(a.run)
