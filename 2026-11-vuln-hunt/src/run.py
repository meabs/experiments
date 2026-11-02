"""Drives one run of one arm on a fresh copy of the target app.

  python3 -I run.py new <run> --arm A|A2|B|C|D --model luna|qwen
  python3 -I run.py go <run>

Runs live in $VH_WORK/<run>/ (default ~/code/benchmark/vh-work): ws/ (the copy of the app the agent reviews, a git
repository), app/ (the database, images and cache of the copy the harness runs for arms A2 to D, outside ws),
FINDINGS.json, meta.json, and for A and A2 codex-home/ and events.jsonl; for B to D transcript.json, tools.jsonl and usage.json.
Run IDs are anonymous; key.json in $VH_WORK maps them to arms.
"""
import argparse, json, os, shutil, socket, subprocess, sys, time

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.environ.get("VH_WORK", os.path.expanduser("~/code/benchmark/vh-work"))
SHOP_PY = os.path.expanduser("~/code/benchmark/venvs/shopapi/bin/python")
STRANDS_PY = os.path.expanduser("~/code/benchmark/venvs/strands/bin/python")
WRAP = os.path.join(E, "setup", "codex-bwrap.sh")
MODELS = {"luna": "openai/gpt-5.6-luna", "qwen": "qwen/qwen3.7-flash"}
CODEX_MODEL, EFFORT = "gpt-5.6-luna", "medium"
GIT = ["git", "-c", "user.name=dev", "-c", "user.email=dev@example.com"]
LIMIT = 2700   # seconds per run


def rdir(run):
    return os.path.join(W, run)


def meta(run):
    return json.load(open(os.path.join(rdir(run), "meta.json")))


def save_meta(run, m):
    json.dump(m, open(os.path.join(rdir(run), "meta.json"), "w"), indent=1)


def new(run, arm, model):
    assert arm in ("A", "A2", "B", "C", "D") and model in MODELS and not (arm in ("A", "A2") and model != "luna")
    d = rdir(run)
    if os.path.exists(d):
        sys.exit(f"{d} exists")
    ws = os.path.join(d, "ws")
    shutil.copytree(os.path.join(E, "target"), ws, ignore=shutil.ignore_patterns("__pycache__", "*.db", ".cache",
                                                                                 "images", "*.egg-info"))
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(GIT + ["add", "-A"], cwd=ws, check=True)
    subprocess.run(GIT + ["commit", "-q", "-m", "shopapi"], cwd=ws, check=True)
    save_meta(run, {"run": run, "arm": arm, "model": CODEX_MODEL if arm in ("A", "A2") else MODELS[model],
                    "effort": EFFORT, "created": time.time()})
    print(d)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_app(d):
    """A seeded copy of the app for the Strands tools; its data lives in d/app, outside the reviewed repository."""
    data = os.path.join(d, "app")
    os.makedirs(data, exist_ok=True)
    env = {**os.environ, "SHOP_DB": os.path.join(data, "shop.db"), "IMAGE_DIR": os.path.join(data, "images"),
           "CACHE_DIR": os.path.join(data, "cache")}
    src = os.path.join(d, "appsrc")          # a separate copy, so the reviewed repository isn't touched
    shutil.copytree(os.path.join(E, "target"), src, ignore=shutil.ignore_patterns("__pycache__", "*.db"))
    subprocess.run([SHOP_PY, "scripts/seed.py"], cwd=src, env=env, check=True, capture_output=True)
    port = free_port()
    p = subprocess.Popen([SHOP_PY, "-c", f"from shopapi import create_app; create_app().run('127.0.0.1', {port})"],
                         cwd=src, env=env, stdout=open(os.path.join(data, "app.log"), "w"), stderr=subprocess.STDOUT,
                         start_new_session=True)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close()
            return p, f"http://127.0.0.1:{port}"
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("app didn't start")


def context(app_url):
    """The same text as reviewers.context (arms B and C), except how to reach the app: Codex has a shell, not the
    http_request tool."""
    return (f"The repository is the current project. A copy of the application is running at {app_url} (paths "
            f"start with /); you can reach it with curl. Today is {time.strftime('%Y-%m-%d')}.")


def go(run):
    m, d = meta(run), rdir(run)
    ws = os.path.join(d, "ws")
    t0 = time.time()
    if m["arm"] in ("A", "A2"):
        task = open(os.path.join(E, "prompts", "task.md")).read().strip()
        app = None
        if m["arm"] == "A2":     # the same checklist and context B gets as its system prompt, ahead of the task
            app, url = start_app(d)
            task = f"{open(os.path.join(E, 'prompts', 'specialist.md')).read().strip()}\n\n{context(url)}\n\n{task}"
            open(os.path.join(d, "prompt.txt"), "w").write(task)
        cmd = ["bash", WRAP, "exec", "--skip-git-repo-check", "--json", "--model", CODEX_MODEL, "-s",
               "danger-full-access", "-c", f'model_reasoning_effort="{EFFORT}"', "-c", 'web_search="disabled"', "-"]
        env = {"RUN_CODEX_HOME": os.path.join(d, "codex-home"), "PATH": "/usr/bin:/bin", "HOME": os.path.expanduser("~")}
        with open(os.path.join(d, "events.jsonl"), "w") as out, open(os.path.join(d, "stderr.txt"), "w") as err:
            p = subprocess.Popen(cmd, cwd=ws, stdin=subprocess.PIPE, text=True, stdout=out, stderr=err, env=env,
                                 start_new_session=True)
            p.stdin.write(task); p.stdin.close()
            try:
                p.wait(timeout=LIMIT); m["stopped"] = None
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, 9); p.wait(); m["stopped"] = "timeout"
        if app:
            os.killpg(app.pid, 9)
        m["exit"] = p.returncode
        m["usage"] = codex_usage(os.path.join(d, "events.jsonl"))
        found = os.path.join(ws, "FINDINGS.json")
        if os.path.exists(found):
            shutil.copy(found, os.path.join(d, "FINDINGS.json"))
    else:
        app, url = start_app(d)
        try:
            arm = {"B": "specialist", "C": "team", "D": "swarm"}[m["arm"]]
            p = subprocess.run([STRANDS_PY, "-I", os.path.join(E, "src", "reviewers.py"), arm, m["model"], ws, url, d],
                               capture_output=True, text=True, timeout=LIMIT)
            m["exit"] = p.returncode
            open(os.path.join(d, "stderr.txt"), "w").write(p.stderr[-20000:])
        except subprocess.TimeoutExpired:
            m["exit"], m["stopped"] = None, "timeout"
        finally:
            os.killpg(app.pid, 9)
        if os.path.exists(os.path.join(d, "usage.json")):
            m["usage"] = json.load(open(os.path.join(d, "usage.json")))
    m["seconds"] = round(time.time() - t0, 1)
    m["findings"] = count(os.path.join(d, "FINDINGS.json"))
    save_meta(run, m)
    print(run, m["arm"], m["model"], "exit", m["exit"], "seconds", m["seconds"], "findings", m["findings"])


def count(path):
    try:
        data = json.load(open(path))
        return len(data) if isinstance(data, list) else None
    except (OSError, ValueError):
        return None


def codex_usage(path):
    u = {"input": 0, "cached": 0, "output": 0, "reasoning": 0, "commands": 0}
    for line in open(path):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "turn.completed":
            us = e.get("usage", {})
            u["input"] += us.get("input_tokens", 0); u["cached"] += us.get("cached_input_tokens", 0)
            u["output"] += us.get("output_tokens", 0); u["reasoning"] += us.get("reasoning_output_tokens", 0)
        if e.get("type") == "item.completed" and e["item"].get("type") == "command_execution":
            u["commands"] += 1
    return u


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["new", "go"])
    ap.add_argument("run")
    ap.add_argument("--arm")
    ap.add_argument("--model", default="luna")
    a = ap.parse_args()
    new(a.run, a.arm, a.model) if a.cmd == "new" else go(a.run)
