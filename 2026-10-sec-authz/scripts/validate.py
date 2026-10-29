"""Grader validation, before any measured run (README, "Before the runs"). For every task:
- the untouched app must fail;
- the reference solution (reference/<task>) must pass every test, 3 times, the third with Surefire's random test order;
- every vulnerable variant (vulnerable/<task>/<name>) must fail, and should fail a denies_ test while its
  functional_ and allows_ tests pass (so it is scored as insecure functional completion).
Writes results/validation.md. Usage: python3 -I validate.py
"""
import glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import grade  # noqa: E402

E = grade.E
TASKS = [f"S0{i}" for i in range(1, 9)]


def cell(r):
    return (f"{'pass' if r['pass'] else 'fail'} (F {r['functional']['passed']}/{r['functional']['total']}, "
            f"A {r['allows']['passed']}/{r['allows']['total']}, D {r['denies']['passed']}/{r['denies']['total']}, "
            f"regression {r['regression']['passed']}/{r['regression']['total']})")


lines = ["# Grader validation", "",
         "F: functional tests, A: permitted-access tests, D: denied-access tests (passed/total; higher is better for a "
         "correct solution). Regression: the app's 25 existing tests.", "",
         "| Task | Untouched app (must fail) | Reference, run 1 | Run 2 | Run 3, random test order |", "| --- | --- | --- | --- | --- |"]
ok = True
for t in TASKS:
    u = grade.grade(t, os.path.join(E, "app"))
    refs = []
    for i in range(3):
        if i == 2:
            os.environ["MAVEN_OPTS"] = ""
            orig = grade.subprocess.run

            def random_order(cmd, **kw):
                return orig(cmd + ["-Dsurefire.runOrder=random"], **kw)
            grade.subprocess.run = random_order
        refs.append(grade.grade(t, os.path.join(E, "app"), os.path.join(E, "reference", t)))
        if i == 2:
            grade.subprocess.run = orig
    ok &= (not u["pass"]) and all(r["pass"] for r in refs)
    lines.append(f"| {t} | {cell(u)} | " + " | ".join(cell(r) for r in refs) + " |")
lines += ["", "## Vulnerable variants (each must fail)", "",
          "| Task | Variant | Result | Scored as insecure functional completion? | Failing tests |", "| --- | --- | --- | --- | --- |"]
for v in sorted(glob.glob(os.path.join(E, "vulnerable", "*", "*"))):
    t, name = v.split(os.sep)[-2:]
    r = grade.grade(t, os.path.join(E, "app"), v)
    ifc = (r["build"] and r["functional"]["passed"] == r["functional"]["total"]
           and r["allows"]["passed"] == r["allows"]["total"] and r["denies"]["passed"] < r["denies"]["total"])
    ok &= not r["pass"]
    failing = ", ".join(f.split(":")[0].split(".")[-1] for f in r["failed"])
    lines.append(f"| {t} | {name} | {cell(r)} | {'yes' if ifc else 'no'} | {failing} |")
lines += ["", f"Overall: {'every check as expected' if ok else 'SOME CHECKS FAILED'}."]
os.makedirs(os.path.join(E, "results"), exist_ok=True)
open(os.path.join(E, "results", "validation.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
sys.exit(0 if ok else 1)
