"""Free self-test (no model): every reference pair goes through unit tests, CI smoke, the oracle and the gate.

Expect: `safe` variants -> oracle clean, rollback recovers, new requirements delivered, gate admits;
        `unsafe` variants -> pass unit tests and CI smoke, oracle finds a violation (or failed rollback), gate rejects.
Writes results/selftest.json. Run: python3 -I scripts/selftest.py [S1 S2 ...]
"""
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import trx  # noqa: E402


def main():
    want = sys.argv[1:] or ["S0", "S1", "S2", "S3", "S4", "S5"]
    res = []
    ok_all = True
    tmp = tempfile.mkdtemp(prefix="trx-selftest-")
    base_jars = os.path.join(tmp, "base")
    print(trx.build(os.path.join(ROOT, "estate"), base_jars))
    for s in want:
        sdir = os.path.join(ROOT, "refs", s)
        for v in sorted(os.listdir(sdir)):
            vdir = os.path.join(sdir, v)
            changed = [d for d in os.listdir(vdir) if os.path.isdir(os.path.join(vdir, d))]
            est = os.path.join(tmp, f"{s}-{v}")
            shutil.copytree(os.path.join(ROOT, "estate"), est, ignore=shutil.ignore_patterns("target", "_common"))
            for svc in changed:
                shutil.copytree(os.path.join(vdir, svc), os.path.join(est, svc), dirs_exist_ok=True)
            jars = os.path.join(tmp, f"jars-{s}-{v}")
            unit = trx.build(est, jars)
            plan = os.path.join(vdir, "plan.txt")
            plan = plan if os.path.exists(plan) else None
            ci = trx.sim("ci", s, jars, jars, changed, None, os.path.join(tmp, f"ci-{s}-{v}.json"))
            rel = trx.sim("release", s, base_jars, jars, changed, plan, os.path.join(tmp, f"rel-{s}-{v}.json"))
            gate = trx.sim("gate", s, base_jars, jars, changed, plan, os.path.join(tmp, f"gate-{s}-{v}.json"))
            viol = rel["violations"]
            rec = rel["recovered"]
            delivered = rel["delivered"]
            safe_expected = v == "safe"
            safe_oracle = (not viol) and rec is not False and delivered and all(delivered.values()) and not rel["aborted"]
            row = {"scenario": s, "variant": v, "changed": changed, "unit": unit, "ci_violations": [x["inv"] for x in ci["violations"]],
                   "oracle_violations": sorted({x["inv"] for x in viol}), "recovered": rec, "delivered": delivered,
                   "failedJourneys": rel["failedJourneys"], "gate": gate["verdict"],
                   "gate_rules": sorted({x["inv"] for r in gate["runs"] for x in r["violations"]})}
            row["ok"] = (unit == "unit ok" and not ci["violations"] and (safe_oracle == safe_expected)
                         and (gate["verdict"] == ("admit" if safe_expected else "reject")))
            ok_all &= row["ok"]
            res.append(row)
            print(("PASS" if row["ok"] else "FAIL"), s, v, json.dumps({k: row[k] for k in ("oracle_violations", "recovered", "delivered", "gate", "gate_rules", "ci_violations", "failedJourneys")}))
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    json.dump(res, open(os.path.join(ROOT, "results", "selftest.json"), "w"), indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    print("ALL OK" if ok_all else "SOME FAILED")
    sys.exit(0 if ok_all else 1)


main()
