"""DEMO ONLY: scripted red and scripted defenders, no model. Shows the viewer; these are not results."""
import sys, os, json, random, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine, make_arch

def minimal_defender(m, seq):
    cands = []
    for s in seq:
        k, x = s.split(":")
        if k == "steal": cands.append([{"op": "set_cred", "id": x, "field": "exposure", "value": "short"}])
        elif k in ("access", "relay"): cands.append([{"op": "set_edge", "id": x, "field": "scope", "value": "none"}])
    for c in cands:
        m2, e = engine.apply_patch(m, c)
        if not e and not engine.flows_broken(m2): return c
    return cands[0] if cands else []

def layer_defender(m, seq, n):
    ops = []
    for s in seq:
        k, x = s.split(":")
        if k == "control":
            v = m["components"][x].get("vuln"); ops.append({"op": "add_mitigation", "component": x, "name": "input_filter" if v == "injectable" else "patched"}); break
    acc = next((s.split(":")[1] for s in seq if s.startswith("access:")), None)
    if acc and acc in m["edges"]:
        e = m["edges"][acc]; gw = f"gw{n}"
        ops += [{"op": "add_component", "id": gw, "kind": "api", "zone": m["components"][e["dst"]]["zone"], "label": f"Gateway {n}"},
                {"op": "add_cred", "id": f"c_{gw}", "holder": gw, "exposure": "plaintext", "lifetime_h": 720, "label": f"{gw} service key"},
                {"op": "add_edge", "id": f"{acc}_in", "src": e["src"], "dst": gw, "scope": e["scope"], "cred": e.get("cred"), "label": "via gateway"},
                {"op": "add_edge", "id": f"{acc}_out", "src": gw, "dst": e["dst"], "scope": e["scope"], "cred": f"c_{gw}", "label": "gateway to service"},
                {"op": "remove_edge", "id": acc}]
    return ops

def play(fixture, arm, rounds=8, seed=1):
    rnd = random.Random(f"{fixture}{arm}{seed}"); m = make_arch.make(fixture); rows = []
    start = engine.metrics(m)
    for r in range(1, rounds + 1):
        paths = engine.attack_paths(m); row = {"round": r, "before": copy.deepcopy(m), "mb": engine.metrics(m)}
        if not paths:
            row.update(seq=[], jewel=None, success=False, ops=[], errors=[], after=copy.deepcopy(m), ma=engine.metrics(m)); rows.append(row); continue
        best = min(len(p[0]) for p in paths); p, j = rnd.choice([p for p in paths if len(p[0]) == best])
        seq = engine.order(m, p); res, jewel = engine.simulate(m, seq)
        ops = [] if arm == "N" else (minimal_defender(m, seq) if arm == "M" else layer_defender(m, seq, r))
        m2, errs = engine.apply_patch(m, ops, "free")
        row.update(seq=seq, jewel=jewel, success=bool(jewel), ops=ops, errors=errs, after=copy.deepcopy(m2), ma=engine.metrics(m2))
        rows.append(row); m = m2
    return {"fixture": fixture, "arm": arm, "start": start, "rounds": rows, "demo": True}

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "results", "demo"); os.makedirs(out, exist_ok=True)
    games = [play(f, a) for f in "AB" for a in ("N", "M", "L")]
    json.dump(games, open(os.path.join(out, "demo-games.json"), "w"))
    for g in games: print(g["fixture"], g["arm"], [r["ma"]["paths"] for r in g["rounds"]], [r["ma"]["complexity"] for r in g["rounds"]])
