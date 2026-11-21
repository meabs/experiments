#!/usr/bin/env python3
"""Crash-resumable local simulation. Standard library only."""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine

ROOT = Path(__file__).resolve().parents[1]
MODEL = "huihui_ai/Qwen3.8-abliterated:latest"
API = "http://127.0.0.1:11434"
STOPPING = False


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def request(endpoint, payload=None, timeout=180):
    req = urllib.request.Request(API + endpoint,
                                 data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def source_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in (ROOT / "scripts", ROOT / "web") for p in sorted(folder.rglob("*"))
            if p.is_file() and p.suffix in (".py", ".html", ".js", ".css")}


class Store:
    def __init__(self, folder, seed=1):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.folder / "world.sqlite3", timeout=30)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, step INTEGER NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS decisions(step INTEGER PRIMARY KEY, town TEXT, actor TEXT,
            parsed INTEGER, accepted INTEGER, input_tokens INTEGER, output_tokens INTEGER,
            seconds REAL, raw_file TEXT, before_hash TEXT, after_hash TEXT);
        CREATE TABLE IF NOT EXISTS snapshots(day INTEGER PRIMARY KEY, step INTEGER, payload TEXT NOT NULL);
        """)
        row = self.db.execute("SELECT value FROM meta WHERE key='world'").fetchone()
        if row is None:
            self.world = engine.new_world(seed)
            with self.db:
                self.db.execute("INSERT INTO meta VALUES ('initial',?)", (engine.canonical(self.world),))
                self.db.execute("INSERT INTO meta VALUES ('world',?)", (engine.canonical(self.world),))
                self.db.execute("INSERT INTO snapshots VALUES (0,0,?)", (engine.canonical(self.world),))
        else:
            self.world = json.loads(row[0])

    def get_meta(self, key, default=None):
        row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_meta(self, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, engine.canonical(value)))

    def commit(self, events, decision=None):
        world = engine.canonical(self.world)
        with self.db:
            self.db.execute("UPDATE meta SET value=? WHERE key='world'", (world,))
            self.db.executemany("INSERT INTO events(step,payload) VALUES (?,?)",
                                [(self.world["step"], engine.canonical(e)) for e in events])
            if decision:
                self.db.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?,?,?,?,?,?)", decision)
            if self.world["step"] % 16 == 0:
                self.db.execute("INSERT OR REPLACE INTO snapshots VALUES (?,?,?)",
                                (self.world["day"] - 1, self.world["step"], world))


def status(folder, **fields):
    atomic(Path(folder) / "status.json", dict(updated_at=time.time(), pid=os.getpid(), **fields))


def stopped(folder):
    return STOPPING or (Path(folder) / "STOP").exists()


def model_metadata(model):
    tags = request("/api/tags")["models"]
    chosen = next((t for t in tags if t["name"].lower() == model.lower()), None)
    if chosen is None:
        raise RuntimeError(f"requested local model absent: {model}")
    return dict(selected=chosen, show=request("/api/show", {"model": model}),
                runtime=request("/api/version"))


def generate(model, observation, seed, deadline):
    payload = dict(model=model, messages=[
        {"role": "system", "content": engine.RULES},
        {"role": "user", "content": engine.canonical(observation)}],
        format=engine.SCHEMA, stream=False, think=False, keep_alive="10m",
        options=dict(num_ctx=8192, num_predict=384, temperature=0.8, seed=seed))
    # Transport retries are visible and bounded. Invalid model output is not retried.
    errors = []
    start = time.time()
    for attempt in range(3):
        try:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError("run deadline reached")
            reply = request("/api/chat", payload, timeout=min(180, remaining))
            return dict(request=payload, response=reply, transport_errors=errors,
                        seconds=time.time() - start)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            errors.append(dict(attempt=attempt + 1, error=str(error)))
            if STOPPING or deadline <= time.time():
                break
            if isinstance(error, urllib.error.HTTPError) and error.code < 500:
                break
            time.sleep(min(5 * (attempt + 1), max(0, deadline - time.time())))
    return dict(request=payload, response=None, transport_errors=errors,
                seconds=time.time() - start)


def run(args):
    folder = Path(args.out).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    lock = (folder / "runner.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    store = Store(folder, args.seed)
    if args.init or args.dry_run:
        result = dict(phase="ready", model=args.model, day=store.world["day"],
                      next_turn=engine.turn(store.world), seed=store.world["seed"])
        if args.dry_run:
            result["observation"] = engine.observation(store.world, *engine.turn(store.world))
        status(folder, **{k: v for k, v in result.items() if k != "observation"})
        print(json.dumps(result, indent=2))
        return 0
    if args.mode == "main":
        gate = ROOT / "results" / "pilot" / "gate.json"
        if not gate.exists() or not json.loads(gate.read_text()).get("passed"):
            raise RuntimeError("main refused: pilot gate has not passed")
    metadata = model_metadata(args.model)
    provenance = dict(model=metadata, sources=source_hashes(), python=sys.version,
                      parameters=dict(context=8192, predict=384, temperature=0.8,
                                      think=False), mode=args.mode, seed=args.seed)
    old = store.get_meta("provenance")
    if old and (old["sources"] != provenance["sources"] or
                old["model"]["selected"]["digest"] != metadata["selected"]["digest"]):
        raise RuntimeError("source/model changed since run began; use a new output directory")
    if not old:
        store.set_meta("provenance", provenance)
        atomic(folder / "provenance.json", provenance)
    deadline = store.get_meta("deadline")
    if deadline is None:
        deadline = time.time() + args.hours * 3600
        store.set_meta("deadline", deadline)
        store.set_meta("started_at", time.time())
    (folder / "decisions").mkdir(exist_ok=True)
    consecutive_errors = 0
    reason = "day_limit"
    while store.world["day"] <= args.rounds:
        if stopped(folder):
            reason = "stop_requested"
            break
        if time.time() >= deadline:
            reason = "24_hour_limit"
            break
        if store.world["step"] >= args.max_calls:
            reason = "call_limit"
            break
        if (folder / "PAUSE").exists():
            status(folder, phase="paused", model=args.model, deadline=deadline)
            time.sleep(2)
            continue
        if store.world["step"] % 16 == 0:
            size = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
            if size >= 1024**3:
                reason = "disk_limit"
                break
            if not any(a["health"] for t in store.world["towns"].values() for a in t["agents"].values()):
                reason = "all_residents_inactive"
                break
        town, who = engine.turn(store.world)
        step = store.world["step"]
        before = engine.digest(store.world)
        events, record = [], None
        if store.world["towns"][town]["agents"][who]["health"]:
            status(folder, phase="thinking", model=args.model, town=town, actor=who,
                   day=store.world["day"], step=step, deadline=deadline, call_started=time.time())
            obs = engine.observation(store.world, town, who)
            raw_path = folder / "decisions" / f"{step:06d}.json.gz"
            # A completed response is written before committing its effects. On crash,
            # reuse that response, never apply a second stochastic choice to the turn.
            if raw_path.exists():
                with gzip.open(raw_path, "rt") as f:
                    raw = json.load(f)
                if raw["before_hash"] != before:
                    raise RuntimeError("orphan response does not match checkpoint")
            else:
                raw = generate(args.model, obs, args.seed * 100000 + step // 2, deadline)
                raw.update(before_hash=before, town=town, actor=who, step=step,
                           recorded_at=time.time())
                tmp = raw_path.with_suffix(".tmp")
                with gzip.open(tmp, "wt") as f:
                    json.dump(raw, f, ensure_ascii=False)
                tmp.replace(raw_path)
            reply = raw["response"]
            if reply is None:
                # An unavailable model must not silently make residents idle or starve.
                # Preserve failed request and stop without advancing this turn.
                status(folder, phase="error", error="local model request failed", detail=raw["transport_errors"],
                       day=store.world["day"], step=step, deadline=deadline)
                failed_path = raw_path.with_name(raw_path.stem + f".failed-{int(time.time())}.gz")
                raw_path.replace(failed_path)
                return 2
            parsed = False
            try:
                decision = json.loads(reply["message"]["content"])
                if not isinstance(decision, dict) or not isinstance(decision.get("action"), dict):
                    raise ValueError("decision/action is not an object")
                parsed = True
                events = engine.apply_decision(store.world, town, who, decision)
                consecutive_errors = 0
            except (ValueError, KeyError, TypeError) as error:
                engine.emit(store.world["towns"][town], events, "invalid_decision", who, str(error))
                consecutive_errors += 1
            accepted = int(any(e["kind"] not in ("rejected", "invalid_decision", "message", "message_rejected") for e in events))
            record = [step, town, who, int(parsed), accepted, reply.get("prompt_eval_count", 0),
                      reply.get("eval_count", 0), raw["seconds"], str(raw_path.relative_to(folder)), before, None]
        store.world["step"] += 1
        if store.world["step"] % 16 == 0:
            events += engine.sunset(store.world)
        if record:
            record[-1] = engine.digest(store.world)
        store.commit(events, record)
        if store.world["step"] % 16 == 0:
            # Verifier has separate arithmetic and reads the committed database.
            from verify import verify
            atomic(folder / "verification.json", verify(folder))
        print(engine.canonical(dict(step=step, day=store.world["day"], town=town, actor=who,
                                    events=[e["detail"] for e in events if e["kind"] != "sunset"])), flush=True)
        if consecutive_errors >= 4:
            reason = "four_consecutive_invalid_decisions"
            break
    status(folder, phase="finished", reason=reason, day=store.world["day"],
           step=store.world["step"], deadline=deadline, model=args.model)
    from analyse import write
    write(folder)
    return 0 if reason in ("day_limit", "24_hour_limit", "call_limit", "disk_limit", "all_residents_inactive", "stop_requested") else 2


def main():
    global STOPPING
    def stop(_sig, _frame):
        global STOPPING
        STOPPING = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--mode", choices=["pilot", "main"], default="main")
    p.add_argument("--model", default=MODEL)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--hours", type=float, default=24)
    p.add_argument("--rounds", type=int, default=10000)
    p.add_argument("--max-calls", type=int, default=20000)
    p.add_argument("--init", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if not 0 < args.hours <= 24 or args.rounds < 1 or not 1 <= args.max_calls <= 20000:
        p.error("hours must be in (0,24], rounds positive, calls 1..20000")
    try:
        return run(args)
    except Exception as error:
        status(args.out, phase="error", error=f"{type(error).__name__}: {error}")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
