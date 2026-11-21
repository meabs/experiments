#!/usr/bin/env python3
"""Owned background supervisor: download -> free checks -> pilot gate -> 24h run."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import API, MODEL, ROOT, Store, atomic, request, source_hashes
from verify import read, verify
from analyse import write

RESULTS = ROOT / "results"
CHILD = None


def progress(phase, **fields):
    atomic(RESULTS / "status.json", dict(phase=phase, updated_at=time.time(),
                                       pid=os.getpid(), **fields))


def stopped():
    return (RESULTS / "STOP").exists()


def execute(script, arguments, log):
    global CHILD
    with (RESULTS / log).open("ab") as output:
        CHILD = subprocess.Popen([sys.executable, "-I", str(ROOT / "scripts" / script), *arguments],
                                 cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
        code = CHILD.wait()
        CHILD = None
    if code:
        raise RuntimeError(f"{script} exited {code}; see results/{log}")


def download():
    progress("downloading", model=MODEL, status="Checking local model storage")
    if any(m["name"].lower() == MODEL.lower() for m in request("/api/tags")["models"]):
        return
    # Streaming progress is bounded to one small atomic status file, no ANSI log flood.
    req = urllib.request.Request(API + "/api/pull", data=json.dumps(dict(model=MODEL, stream=True)).encode(),
                                 headers={"Content-Type": "application/json"})
    last_write = 0
    with urllib.request.urlopen(req, timeout=180) as response:
        for line in response:
            if stopped():
                return
            item = json.loads(line)
            if item.get("error"):
                raise RuntimeError(item["error"])
            if time.time() - last_write >= 2 or item.get("status") == "success":
                progress("downloading", model=MODEL, **item)
                last_write = time.time()


def supervise(hours):
    lock = (RESULTS / "supervisor.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        if stopped():
            progress("stopped", reason="STOP file exists; explicit restart required")
            return
        download()
        if stopped():
            progress("stopped", reason="Stopped during download")
            return
        progress("selftest")
        execute("selftest.py", [], "selftest.log")
        execute("run.py", ["--out", str(RESULTS / "dry-run"), "--dry-run"], "dry-run.log")
        atomic(RESULTS / "design-freeze.json", dict(frozen_at=time.time(), sources=source_hashes(),
                                                    readme_sha256=__import__('hashlib').sha256((ROOT / "README.md").read_bytes()).hexdigest()))
        pilot = RESULTS / "pilot"
        pilot.mkdir(exist_ok=True)
        (pilot / "PILOT-ONLY").write_text("Technical pilot only. Excluded from main.\n")
        progress("pilot")
        execute("run.py", ["--mode", "pilot", "--rounds", "1", "--hours", "2", "--out", str(pilot)], "pilot.log")
        meta, _, decisions = read(pilot)
        verification = verify(pilot)
        calls = len(decisions)
        parsed = sum(d[3] for d in decisions)
        accepted = sum(d[4] for d in decisions)
        free = json.loads((RESULTS / "selftest.json").read_text())
        gate = dict(passed=calls >= 16 and parsed / calls >= .75 and accepted / calls >= .5
                    and verification["passed"] and free["passed"] and meta["world"]["day"] >= 2,
                    calls=calls, parsed=parsed, accepted=accepted, verification=verification,
                    selftest=free["passed"], checked_at=time.time())
        atomic(pilot / "gate.json", gate)
        write(pilot)
        if not gate["passed"]:
            raise RuntimeError("Pilot failed its written gate; main was not launched. Inspect results/pilot/gate.json")
        if stopped():
            progress("stopped", reason="Stopped after pilot")
            return
        progress("running", model=MODEL, hours=hours)
        execute("run.py", ["--mode", "main", "--hours", str(hours), "--out", str(RESULTS / "main")], "main.log")
        result = json.loads((RESULTS / "main" / "status.json").read_text())
        progress("finished", reason=result.get("reason"), model=MODEL)
    except Exception as error:
        progress("error", error=f"{type(error).__name__}: {error}")
        raise


def launch(args):
    RESULTS.mkdir(exist_ok=True)
    Store(RESULTS / "main").db.close()
    if (RESULTS / "STOP").exists():
        raise RuntimeError("STOP file exists. Keep existing records; remove STOP deliberately to resume.")
    pids = {}
    for name, command in (("observer", ["serve.py", "--port", str(args.port)]),
                           ("supervisor", ["manage.py", "supervise", "--hours", str(args.hours)])):
        # fcntl lock guards the supervisor; loopback port guards the observer.
        log = (RESULTS / f"{name}.log").open("ab")
        child = subprocess.Popen([sys.executable, "-I", str(ROOT / "scripts" / command[0]), *command[1:]],
                                  cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                  stdin=subprocess.DEVNULL, start_new_session=True)
        log.close()
        pids[name] = child.pid
        (RESULTS / f"{name}.pid").write_text(str(child.pid) + "\n")
    atomic(RESULTS / "processes.json", dict(started_at=time.time(), pids=pids,
                                           observer_url=f"http://127.0.0.1:{args.port}"))
    print(json.dumps(dict(**pids, url=f"http://127.0.0.1:{args.port}",
                         pipeline="download -> selftest -> pilot -> main, 24h maximum"), indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["start", "supervise", "status", "stop"])
    p.add_argument("--hours", type=float, default=24)
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()
    if not 0 < args.hours <= 24:
        p.error("hours must be in (0,24]")
    if args.command == "start":
        launch(args)
    elif args.command == "supervise":
        def stop(sig, frame):
            (RESULTS / "STOP").touch()
            (RESULTS / "main" / "STOP").touch()
            if CHILD:
                CHILD.send_signal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        supervise(args.hours)
    elif args.command == "stop":
        (RESULTS / "STOP").touch()
        (RESULTS / "main" / "STOP").touch()
        print("Stop requested. Current call may finish; all records retained.")
    else:
        print((RESULTS / "status.json").read_text())
