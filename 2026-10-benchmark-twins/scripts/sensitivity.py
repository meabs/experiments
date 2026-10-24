"""Post-hoc sensitivity check, added after the results (REPORT, "Exploratory"). Not part of the preregistered analysis.

After a failed tool call, the local model sometimes put its final answer in a reasoning item rather than a message, so
Codex recorded no final message and the reply was graded as no answer. This regrades those replies from the text of the
last reasoning item, with the same parsing and grading as run.py, and re-runs the H1 to H4 comparisons unadjusted.
Usage: python3 -I sensitivity.py <results stage dir> <items dir>
"""
import glob, gzip, json, os, re, statistics as st, sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from grade_code import run_tests  # noqa: E402
from signflip_dp import signflip_exact  # noqa: E402

D, I = sys.argv[1:3]
ANSWER = re.compile(r"ANSWER:\s*\**\s*\$?\s*(-?[\d,]*\.?\d+)")
CODE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)
items = {"gsm8k": {x["idx"]: x for x in json.load(open(os.path.join(I, "gsm8k-twins.json")))},
         "humaneval": {x["idx"]: x for x in json.load(open(os.path.join(I, "humaneval-twins-sample.json")))}}
R, changed = {}, []
for f in glob.glob(os.path.join(D, "*", "*", "*", "*", "result.json")):
    m, b, v, i = f.split(os.sep)[-5:-1]; i = int(i)
    r = json.load(open(f)); ok = bool(r["correct"])
    if r["answer"] is None:
        last = ""
        for line in gzip.open(os.path.join(os.path.dirname(f), "raw.out.gz"), "rt"):
            try:
                it = json.loads(line).get("item") or {}
            except ValueError:
                continue
            if it.get("type") == "reasoning" and json.loads(line).get("type") == "item.completed":
                last = it.get("text", "")
        it = items[b][i]
        if b == "gsm8k":
            a = ANSWER.findall(last)
            ref = it["answer_orig"] if v in ("orig", "names") else it["answer_twin"]
            ok = bool(a) and F(a[-1].replace(",", "")) == F(str(ref))
        else:
            c = CODE.findall(last)
            ok = bool(c) and run_tests(it[v] + "\n" + c[-1], it[f"test_{v}"], it[f"entry_{v}"])[0]
        changed.append((m, b, v, i, ok))
    R[(m, b, v, i)] = int(ok)
print(f"Regraded {len(changed)} replies with no final message; now right: {sum(c[4] for c in changed)}.\n")
print("| model | benchmark | variant | right after regrading |\n| --- | --- | --- | --- |")
for m in ("local", "hosted"):
    for b, vs in (("gsm8k", ["orig", "numbers", "names", "both"]), ("humaneval", ["orig", "renamed"])):
        for v in vs:
            ks = [k for k in R if k[:3] == (m, b, v)]
            print(f"| {m} | {b} | {v} | {sum(R[k] for k in ks)}/{len(ks)} |")


def d(m, b, w):
    return [R[(m, b, "orig", i)] - R[(m, b, w, i)] for (mm, bb, vv, i) in R if (mm, bb, vv) == (m, b, w)]


print("\n| comparison | orig right only / same / twin right only | mean effect | p (unadjusted) |\n| --- | --- | --- | --- |")
rows = [("H1 local, GSM8K numbers", d("local", "gsm8k", "numbers"), False), ("H2 local, GSM8K names", d("local", "gsm8k", "names"), False),
        ("H3 local, HumanEval renamed", d("local", "humaneval", "renamed"), False),
        ("H4 numbers drop, local vs hosted", [a - b for a, b in zip(
            [R[("local", "gsm8k", "orig", i)] - R[("local", "gsm8k", "numbers", i)] for i in sorted(items["gsm8k"])],
            [R[("hosted", "gsm8k", "orig", i)] - R[("hosted", "gsm8k", "numbers", i)] for i in sorted(items["gsm8k"])])], True)]
for name, x, two in rows:
    print(f"| {name} | {sum(v > 0 for v in x)} / {sum(v == 0 for v in x)} / {sum(v < 0 for v in x)} | {st.mean(x) * 100:+.1f} pts | {signflip_exact(x, two):.4f} |")
