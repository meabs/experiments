"""Shared helpers: build the estate, run the simulator, merge release plans."""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def build(estate_dir, jars_dir):
    out = subprocess.run(["bash", os.path.join(HERE, "build_estate.sh"), estate_dir, jars_dir], capture_output=True, text=True)
    return out.stdout.strip()


def sim(mode, scen, old, new, changed, plan, out, timeout=300):
    cmd = ["bash", os.path.join(HERE, "sim.sh"), mode, scen, "--old", old, "--new", new, "--changed", ",".join(changed), "--out", out]
    if plan:
        cmd += ["--plan", plan]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError("sim failed: " + p.stderr[-800:])
    return json.load(open(out))


def merge_plans(constraints, changed):
    """constraints: {service: {"deploy_after": [...], "atomic_with": [...], "drain_before": bool}} from each team's release/plan.json.
    Returns plan text for the simulator (`stage a,b [drain]` lines), or None to use the default (alphabetical, one by one)."""
    if not constraints:
        return None
    svcs = sorted(changed)
    group = {s: {s} for s in svcs}
    for s, c in constraints.items():
        for o in c.get("atomic_with", []):
            if o in group and s in group:
                u = group[s] | group[o]
                for x in u:
                    group[x] = u
    nodes = sorted({frozenset(g) for g in group.values()}, key=lambda g: sorted(g))
    node_of = {s: n for n in nodes for s in n}
    after = {n: set() for n in nodes}
    for s, c in constraints.items():
        if s not in node_of:
            continue
        for o in c.get("deploy_after", []):
            if o in node_of and node_of[o] != node_of[s]:
                after[node_of[s]].add(node_of[o])
    order, done = [], set()
    while len(done) < len(nodes):
        ready = [n for n in nodes if n not in done and after[n] <= done]
        if not ready:
            return None  # cycle: fall back to the default
        n = ready[0]
        done.add(n)
        order.append(n)
    lines = []
    for n in order:
        drain = any(constraints.get(s, {}).get("drain_before") for s in n)
        lines.append("stage " + ",".join(sorted(n)) + (" drain" if drain else ""))
    return "\n".join(lines) + "\n"
