"""One game: python3 -I run_game.py <fixture> <arm N|F|S|M> <rep> <out.json> [--rounds 8] [--model qwen3.8:27b]
Red (and the defender in F and S) are local Ollama calls; the engine decides every outcome."""
import sys, os, json, time, re, copy, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine, make_arch
from demo import minimal_defender

MODEL = "qwen3.8:27b"; URL = "http://127.0.0.1:11434/api/chat"
def chat(system, user, seed, model=MODEL, timeout=900):
    body = {"model": model, "stream": False, "think": False, "format": "json",
            "options": {"temperature": 0.7, "seed": seed, "num_ctx": 8192, "num_predict": 1800},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    t = time.time()
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return r["message"]["content"], {"in": r.get("prompt_eval_count", 0), "out": r.get("eval_count", 0), "sec": round(time.time() - t, 1)}
def parse(txt):
    try: return json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S)
        try: return json.loads(m.group(0)) if m else None
        except Exception: return None

def documented(m):
    return {"zones": m["zones"],
            "components": {i: {"label": c["label"], "kind": c["kind"], "zone": c["zone"]} for i, c in m["components"].items()},
            "edges": {i: {"from": e["src"], "to": e["dst"], "scope": e["scope"], "needs_credential": e.get("cred"), "label": e["label"]} for i, e in m["edges"].items()},
            "credentials": {i: {"label": c["label"], "held_by": c["holder"]} for i, c in m["creds"].items()}}

RED = """You are the red team in a security exercise on a FICTIONAL system model. Nothing real is attacked. You start as 'internet'.
Goal: reach a crown jewel (customer_db, ledger, or vault). You see the documented architecture, not its hidden weaknesses.
Propose an attack as an ordered list of steps. Step forms (exactly):
  access:<edge_id>    use an edge from a component you already control (or from 'internet'); it needs its credential unless you hold it or control the component that holds it
  relay:<edge_id>     untrusted text you can submit flows along a 'relays' edge to an agent
  control:<component_id>  take over a component you have access to, if it has an exploitable weakness (you cannot see which do)
  steal:<credential_id>   take a credential from a component you control, if it is stored badly
Reply with JSON only: {"reasoning": "<two sentences>", "steps": ["access:...", ...]}. At most 8 steps."""
DEF = """You are the defender (system owner) of a FICTIONAL system model. A red team just breached it with a verified attack.
Change the live architecture so this attack no longer works, WITHOUT breaking the business flows listed (each must still be possible).
Reply with JSON only: {"reason": "<one sentence>", "ops": [ ... ]}. Allowed ops (JSON objects):
  {"op":"remove_edge","id":E}  {"op":"set_edge","id":E,"field":"scope","value":"none|read|write|admin"}
  {"op":"remove_cred","id":C}  {"op":"set_cred","id":C,"field":"exposure","value":"plaintext|vault|short"}  {"op":"set_cred","id":C,"field":"lifetime_h","value":N}
  {"op":"remove_component","id":X}
  {"op":"add_mitigation","component":X,"name":"input_filter|approval_gate|patched|sandbox"}
  {"op":"add_component","id":X,"kind":"api|agent|store|vault","zone":"dmz|internal|data|admin","label":"..."}
  {"op":"add_edge","id":E,"src":X,"dst":Y,"scope":"read|write","cred":C or null,"label":"..."}
  {"op":"add_cred","id":C,"holder":X,"exposure":"plaintext|vault|short","lifetime_h":N,"label":"..."}
Mitigation names: input_filter or approval_gate stop prompt injection of an agent; patched or sandbox stop remote code execution."""
DEF_S = DEF + "\nRESTRICTION: you may only remove or narrow things (remove_*, set_edge to a lower scope, set_cred to a safer exposure or shorter lifetime). add_* ops are rejected."

def play(fixture, arm, rep, rounds=8, model=MODEL):
    m = make_arch.make(fixture); rows = []; calls = []; hist = []; start = engine.metrics(m); zero = 0
    for r in range(1, rounds + 1):
        row = {"round": r, "before": copy.deepcopy(m), "mb": engine.metrics(m), "attempts": []}
        seq, jewel = [], None
        for a in range(3):
            u = "DOCUMENTED ARCHITECTURE:\n" + json.dumps(documented(m)) + "\n\nEARLIER ROUNDS:\n" + ("\n".join(hist) or "none") + \
                ("\n\nYOUR ATTEMPTS THIS ROUND:\n" + "\n".join(row["attempts"]) if row["attempts"] else "") + "\n\nPropose your attack."
            txt, usage = chat(RED, u, seed=rep * 1000 + r * 10 + a, model=model); calls.append({"who": "red", "round": r, **usage})
            d = parse(txt); steps = d.get("steps") if isinstance(d, dict) else None
            if not isinstance(steps, list) or not all(isinstance(s, str) for s in steps):
                row["attempts"].append(f"attempt {a+1}: unparseable reply"); continue
            steps = steps[:8]; res, j = engine.simulate(m, steps)
            row["attempts"].append(f"attempt {a+1}: {steps} -> step results {res}" + (" -> BREACH" if j else " -> failed"))
            if j: seq, jewel = [s for s, ok in zip(steps, res) if ok], j; break
        row["seq"] = seq; row["jewel"] = jewel; row["success"] = bool(jewel); ops, errs = [], []
        if jewel:
            hist.append(f"round {r}: breach via {seq}")
            if arm == "M": ops = minimal_defender(m, engine.order(m, seq))
            elif arm in ("F", "S"):
                flows = [f[2] for f in m["flows"]]
                u = "ARCHITECTURE:\n" + json.dumps(m["components"] | {}, default=str)[:0] + json.dumps({"components": {i: {k: v for k, v in c.items() if k != "vuln"} for i, c in m["components"].items()}, "edges": m["edges"], "credentials": m["creds"]}) + \
                    "\n\nVERIFIED ATTACK (steps that worked, in order): " + json.dumps(seq) + "\nReached: " + jewel + "\nBUSINESS FLOWS THAT MUST KEEP WORKING: " + json.dumps(m["flows"]) + "\n\nPropose your change."
                for t in range(2):
                    txt, usage = chat(DEF_S if arm == "S" else DEF, u + ("\n\nYour last proposal was rejected: " + "; ".join(errs) if errs else ""), seed=rep * 1000 + r * 10 + 5 + t, model=model)
                    calls.append({"who": "def", "round": r, **usage}); d = parse(txt)
                    ops = d.get("ops") if isinstance(d, dict) and isinstance(d.get("ops"), list) else []
                    ops = [o for o in ops if isinstance(o, dict)]
                    _, errs = engine.apply_patch(m, ops, "subtractive" if arm == "S" else "free")
                    if not errs: break
                    row["rejected_ops"] = ops
                if errs: ops = []
        m2, errs2 = engine.apply_patch(m, ops, "subtractive" if arm == "S" else "free")
        row.update(ops=ops if not errs2 else [], errors=errs if arm in ("F", "S") and errs else errs2, after=copy.deepcopy(m2), ma=engine.metrics(m2))
        row["new_paths"] = [p for p in map(tuple, (x[0] for x in engine.attack_paths(m2))) if p not in set(tuple(x[0]) for x in engine.attack_paths(m))]
        rows.append(row); m = m2
        zero = zero + 1 if row["ma"]["paths"] == 0 else 0
        if zero >= 2 and arm != "N": break
    return {"fixture": fixture, "arm": arm, "rep": rep, "model": model, "start": start, "rounds": rows, "calls": calls}

if __name__ == "__main__":
    a = sys.argv; rounds = int(a[a.index("--rounds") + 1]) if "--rounds" in a else 8
    model = a[a.index("--model") + 1] if "--model" in a else MODEL
    g = play(a[1], a[2], int(a[3]), rounds, model); json.dump(g, open(a[4], "w"))
    c = g["calls"]; print(a[1], a[2], "paths", [r["ma"]["paths"] for r in g["rounds"]], "cx", [r["ma"]["complexity"] for r in g["rounds"]],
        "calls", len(c), "sec", sum(x["sec"] for x in c), "tok", sum(x["in"] for x in c), sum(x["out"] for x in c))
