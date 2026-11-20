"""Rule engine for the architecture model. Deterministic, no model.
Facts: C(x) attacker controls component x; A(x) attacker has access to x; H(c) attacker holds credential c."""
import copy, itertools
SCOPE = {"none": 0, "read": 1, "write": 2, "admin": 3}
EXPO = {"short": 0, "vault": 1, "plaintext": 2}
CAP = 40

def vuln_active(comp):
    v, m = comp.get("vuln"), set(comp.get("mitigations", []))
    if v == "injectable": return not (m & {"input_filter", "approval_gate"})
    if v == "rce": return not (m & {"patched", "sandbox"})
    return False

def edge_cred_ok(model, e, held, controlled):
    """Can an attacker controlling e.src (and holding `held`) use this edge?"""
    if e["scope"] == "none": return False
    c = e.get("cred")
    if c is None: return True
    cr = model["creds"].get(c)
    if cr is None: return False            # dangling credential: nobody can use it
    return c in held or cr["holder"] == e["src"]

def actions(model):
    """(name, preconditions[list of facts], effect fact)."""
    out = []
    for eid, e in model["edges"].items():
        if e["scope"] == "none": continue
        c = e.get("cred"); pre = [("C", e["src"])]
        if c is not None:
            cr = model["creds"].get(c)
            if cr is None: continue
            if cr["holder"] != e["src"]: pre.append(("H", c))
        out.append((f"access:{eid}", pre, ("A", e["dst"])))
    for eid, e in model["edges"].items():
        if e.get("relay") and e["scope"] != "none":
            out.append((f"relay:{eid}", [("A", e["src"])], ("A", e["dst"])))
    for cid, comp in model["components"].items():
        if vuln_active(comp): out.append((f"control:{cid}", [("A", cid)], ("C", cid)))
    vaults = [i for i, c in model["components"].items() if c["kind"] == "vault"]
    for cid, cr in model["creds"].items():
        if cr["holder"] not in model["components"]: continue
        if cr["exposure"] == "plaintext": out.append((f"steal:{cid}", [("C", cr["holder"])], ("H", cid)))
        elif cr["exposure"] == "vault":
            for v in vaults: out.append((f"steal:{cid}", [("C", v)], ("H", cid)))
    return out

def minimise(sets):
    sets = sorted(set(sets), key=lambda s: (len(s), sorted(s)))
    keep = []
    for s in sets:
        if not any(k <= s for k in keep): keep.append(s)
    return keep[:CAP]

def proofs(model):
    acts = actions(model)
    P = {("C", "internet"): [frozenset()]}
    for _ in range(12):
        changed = False
        for name, pre, eff in acts:
            if any(p not in P for p in pre): continue
            combos = [frozenset()]
            for p in pre:
                combos = minimise([a | b for a in combos for b in P[p]])
            new = minimise([c | {name} for c in combos] + P.get(eff, []))
            if new != P.get(eff): P[eff] = new; changed = True
        if not changed: break
    return P

def attack_paths(model):
    """Distinct minimal action sets from the internet to any crown jewel."""
    P = proofs(model); out = {}
    for j, c in model["components"].items():
        if c.get("jewel"):
            for key in (("A", j), ("C", j)):
                for s in P.get(key, []): out.setdefault(s, j)
    ps = minimise(list(out))
    return [(sorted(s), out[s]) for s in ps]

def order(model, path):
    """Order an action set so each step is enabled by earlier ones."""
    acts = {n: (pre, eff) for n, pre, eff in actions(model)}
    facts = {("C", "internet")}; seq = []; left = list(path)
    while left:
        for n in left:
            if all(p in facts for p in acts[n][0]):
                facts.add(acts[n][1]); seq.append(n); left.remove(n); break
        else: return seq + left
    return seq

def simulate(model, steps):
    """Run a red-proposed step list. Returns (results, jewel reached)."""
    acts = {}
    for n, pre, eff in actions(model): acts.setdefault(n, []).append((pre, eff))
    facts = {("C", "internet")}; res = []
    for s in steps:
        ok = False
        for pre, eff in acts.get(s, []):
            if all(p in facts for p in pre): facts.add(eff); ok = True; break
        res.append(ok)
    jewel = next((j for j, c in model["components"].items() if c.get("jewel") and (("A", j) in facts or ("C", j) in facts)), None)
    return res, jewel   # failed side steps do not undo what worked

def flows_broken(model):
    broken = []
    for src, dst, label in model["flows"]:
        seen, todo = {src}, [src]
        while todo:
            x = todo.pop()
            for e in model["edges"].values():
                if e["src"] == x and e["scope"] != "none" and e["dst"] not in seen:
                    c = e.get("cred")
                    if c is None or (c in model["creds"] and model["creds"][c]["holder"] == x):
                        seen.add(e["dst"]); todo.append(e["dst"])
        if dst not in seen: broken.append(label)
    return broken

def complexity(model):
    return {"components": len(model["components"]), "edges": len(model["edges"]), "creds": len(model["creds"]),
            "mitigations": sum(len(c.get("mitigations", [])) for c in model["components"].values())}

def total(model): return sum(complexity(model).values())

def metrics(model):
    p = attack_paths(model)
    return {"paths": len(p), "complexity": total(model), **complexity(model), "flows_broken": flows_broken(model)}

# ---- patches
def apply_patch(model, ops, mode="free"):
    m = copy.deepcopy(model); errs = []
    def bad(msg): errs.append(msg)
    for op in ops:
        k = op.get("op")
        try:
            if mode == "subtractive" and k.startswith("add_"): bad(f"{k} not allowed in subtractive mode"); continue
            if k == "add_component":
                if op["id"] in m["components"]: bad("duplicate component"); continue
                m["components"][op["id"]] = {"kind": op["kind"], "zone": op["zone"], "label": op.get("label", op["id"]),
                                             "mitigations": [], **({"vuln": op["vuln"]} if op.get("vuln") else {})}
            elif k == "remove_component":
                if op["id"] in ("internet",) or m["components"].get(op["id"], {}).get("jewel"): bad("cannot remove that"); continue
                m["components"].pop(op["id"])
                m["edges"] = {i: e for i, e in m["edges"].items() if op["id"] not in (e["src"], e["dst"])}
                m["creds"] = {i: c for i, c in m["creds"].items() if c["holder"] != op["id"]}
            elif k == "add_edge":
                if op["id"] in m["edges"] or op["src"] not in m["components"] or op["dst"] not in m["components"]: bad("bad edge"); continue
                m["edges"][op["id"]] = {"src": op["src"], "dst": op["dst"], "scope": op["scope"], "cred": op.get("cred"), "label": op.get("label", op["id"])}
            elif k == "remove_edge":
                if op["id"] not in m["edges"]: bad("no such edge"); continue
                m["edges"].pop(op["id"])
            elif k == "set_edge":
                e = m["edges"].get(op["id"])
                if e is None or op["field"] not in ("scope", "cred"): bad("bad set_edge"); continue
                if mode == "subtractive" and (op["field"] != "scope" or SCOPE[op["value"]] > SCOPE[e["scope"]]): bad("not a narrowing"); continue
                if op["field"] == "scope" and op["value"] not in SCOPE: bad("bad scope"); continue
                e[op["field"]] = op["value"]
            elif k == "add_cred":
                if op["id"] in m["creds"] or op["holder"] not in m["components"] or op["exposure"] not in EXPO: bad("bad cred"); continue
                m["creds"][op["id"]] = {"holder": op["holder"], "exposure": op["exposure"], "lifetime_h": op.get("lifetime_h", 1), "label": op.get("label", op["id"])}
            elif k == "remove_cred":
                if op["id"] not in m["creds"]: bad("no such cred"); continue
                m["creds"].pop(op["id"])
            elif k == "set_cred":
                c = m["creds"].get(op["id"])
                if c is None or op["field"] not in ("exposure", "lifetime_h"): bad("bad set_cred"); continue
                if op["field"] == "exposure" and op["value"] not in EXPO: bad("bad exposure"); continue
                if mode == "subtractive" and ((op["field"] == "exposure" and EXPO[op["value"]] > EXPO[c["exposure"]]) or (op["field"] == "lifetime_h" and op["value"] > c["lifetime_h"])): bad("not a narrowing"); continue
                c[op["field"]] = op["value"]
            elif k == "add_mitigation":
                c = m["components"].get(op["component"])
                if c is None: bad("no such component"); continue
                c.setdefault("mitigations", []).append(op["name"])
            else: bad(f"unknown op {k}")
        except (KeyError, TypeError) as ex: bad(f"malformed {k}: {ex}")
    return (m if not errs else model), errs
