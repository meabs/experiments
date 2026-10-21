"""F1 per question against the truth, as in Experiment 3 (multihop.py). Usage: grade_qa.py <truth> <answer> <out json>."""
import json, os, re, sys

truth = json.load(open(sys.argv[1]))["truth"]
text = open(sys.argv[2], errors="replace").read() if os.path.exists(sys.argv[2]) else ""
ans = {}
for line in text.splitlines():
    m = re.match(r"^\W*(M\d+)\s*[:.)\]\*]+\s*(.*)$", line)
    if m:
        ans[m.group(1)] = set(re.findall(r"[A-Z][A-Za-z0-9_]*", m.group(2)))
res = {}
for q, t in truth.items():
    t, a = set(t), ans.get(q)
    if a is None:
        res[q] = 0.0
        continue
    tp = len(a & t)
    p = tp / len(a) if a else 0.0
    r = tp / len(t) if t else 1.0
    res[q] = round(2 * p * r / (p + r), 3) if p + r else 0.0
mean = round(sum(res.values()) / len(res), 3)
out = {"answer_found": bool(text), "f1": res, "mean_f1": mean, "exact": sum(v == 1.0 for v in res.values()), "pass": mean >= 0.95}
json.dump(out, open(sys.argv[3], "w"), indent=1)
sys.exit(0 if out["pass"] else 1)
