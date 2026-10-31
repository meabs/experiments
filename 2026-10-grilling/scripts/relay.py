"""Relay for the interview arms (Q, G, GD): the developer sees only an anonymous ID, the task and the agent's message.

  python3 -I relay.py setup                 creates the 54 runs under anonymous IDs (key in $GRILL_WORK/key.json)
  python3 -I relay.py start ID [ID...]      first turns, in parallel; prints each agent message
  python3 -I relay.py reply ID FILE LABELS  sends the developer's reply (FILE) and saves its labels (JSON), prints the answer
  python3 -I relay.py list                  each ID: task, turns, whether src/main changed, graded
"""
import json, os, random, secrets, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

S = os.path.dirname(os.path.abspath(__file__))
W = os.environ.get("GRILL_WORK", os.path.expanduser("~/code/benchmark/grilling-work"))
KEY = os.path.join(W, "key.json")
sys.path.insert(0, S)
import run as R  # noqa: E402


def setup():
    if os.path.exists(KEY):
        sys.exit("key exists")
    key = {}
    cells = [(t, a, i) for t in ["C1", "C2", "S1", "S2", "L1", "L2"] for a in ["Q", "G", "GD"] for i in (1, 2, 3)]
    random.SystemRandom().shuffle(cells)
    for n, (t, a, i) in enumerate(cells):
        rid = f"i{n + 1:02d}-{secrets.token_hex(2)}"
        key[rid] = {"task": t, "arm": a, "rep": i}
        subprocess.run([sys.executable, "-I", os.path.join(S, "run.py"), "new", rid, "--task", t, "--arm", a],
                       check=True, stdout=subprocess.DEVNULL)
    json.dump(key, open(KEY, "w"), indent=1)
    print(len(key), "runs; order is the ID number")


def show(rid, reply, code):
    print(f"===== {rid} task {R.meta(rid)['task']} turn {R.meta(rid)['turns']} exit {code} "
          f"src/main changed {R.changed_main(rid)}\n{reply}\n")


def start(ids):
    with ThreadPoolExecutor(3) as ex:
        for rid, (reply, code) in zip(ids, ex.map(lambda r: R.turn(r), ids)):
            show(rid, reply, code)


def reply(rid, f, labels):
    lab = json.loads(labels)
    n = R.meta(rid)["turns"] + 1
    json.dump(lab, open(os.path.join(R.rdir(rid), "turns", f"{n:02d}.labels.json"), "w"))
    r, code = R.turn(rid, open(f).read().strip())
    show(rid, r, code)


def lst():
    for rid in sorted(json.load(open(KEY))):
        m = R.meta(rid)
        print(rid, m["task"], "turns", m["turns"], "changed", R.changed_main(rid),
              "graded", os.path.exists(os.path.join(R.rdir(rid), "grade.json")))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "setup":
        setup()
    elif c == "start":
        start(sys.argv[2:])
    elif c == "reply":
        reply(sys.argv[2], sys.argv[3], sys.argv[4])
    elif c == "list":
        lst()
