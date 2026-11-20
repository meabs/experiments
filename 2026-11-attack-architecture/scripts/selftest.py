import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine, make_arch
ok = True
def check(name, cond):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name)
for n in "ABCD":
    m = make_arch.make(n); paths = engine.attack_paths(m)
    check(f"{n}: has attack paths and no broken flows", len(paths) >= 2 and not engine.flows_broken(m))
    seq = engine.order(m, paths[0][0]); res, jewel = engine.simulate(m, seq)
    check(f"{n}: known attack succeeds ({jewel})", all(res) and jewel)
    check(f"{n}: forged step rejected", engine.simulate(m, ["control:ledger"]) == ([False], None))
    check(f"{n}: reversed order rejected", not all(engine.simulate(m, seq[::-1])[0]) or len(seq) == 1)
    # exact fix: cut the first access edge of the known attack
    eid = next(s.split(":")[1] for s in seq if s.startswith("access:"))
    m2, errs = engine.apply_patch(m, [{"op": "set_edge", "id": eid, "field": "scope", "value": "none"}])
    check(f"{n}: exact fix removes that attack", not errs and tuple(paths[0][0]) not in [tuple(p[0]) for p in engine.attack_paths(m2)])
    # harmful shortcut: delete the jewel's inbound edges. Paths vanish, business flows break.
    ops = [{"op": "remove_edge", "id": i} for i, e in m["edges"].items() if m["components"][e["dst"]].get("jewel")]
    m3, errs = engine.apply_patch(m, ops)
    check(f"{n}: shortcut removes every path", not errs and engine.metrics(m3)["paths"] == 0)
    check(f"{n}: shortcut caught as breaking flows", len(engine.flows_broken(m3)) >= 3)
    m4, errs = engine.apply_patch(m, [{"op": "add_edge", "id": "x", "src": "nope", "dst": "web", "scope": "read"}])
    check(f"{n}: invalid patch rejected, model unchanged", errs and m4 == m)
    m5, errs = engine.apply_patch(m, [{"op": "add_component", "id": "gw", "kind": "api", "zone": "dmz"}], "subtractive")
    check(f"{n}: subtractive mode refuses additions", errs)
    m6, errs = engine.apply_patch(m, [{"op": "set_edge", "id": eid, "field": "scope", "value": "admin"}], "subtractive")
    check(f"{n}: subtractive mode refuses widening", errs)
print("ALL PASS" if ok else "FAILURES"); raise SystemExit(0 if ok else 1)
