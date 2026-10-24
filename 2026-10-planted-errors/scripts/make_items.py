"""Builds the items and the planted values (README, "Items"). No language model is used.

Uses the GSM8K replay from 2026-10-benchmark-twins (make_gsm8k_twins.analyse): every calculator step of the reference
solution is replayed with exact fractions. Items with 3 or more steps are kept. Two steps per item get a planted value:
early = the first step, late = the second-to-last step. The planted value is the step's result moved by 10% to 50% (at
least 1), drawn with random.Random(1000 * item index + step); the later steps are replayed with it to get the
"follows the error" answer. A plant is kept only if the planted value is a positive whole number, the follow answer is a
positive whole number different from the right answer, and the step's true result does not appear among the question's
numbers (so "= <result>" in the model's thinking can only be that step). Up to 200 draws per step.
Usage: python3 -I make_items.py <gsm8k test.jsonl> <out.json>
"""
import json, math, os, random, sys
from fractions import Fraction as F

X = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(X, "2026-10-benchmark-twins", "scripts"))
import make_gsm8k_twins as tw  # noqa: E402


def replay_from(prog, vals, k, planted):
    """Replays the steps with step k's result replaced by `planted`."""
    res = []
    for i, ops in enumerate(prog):
        if i == k:
            res.append(F(planted)); continue
        res.append(tw.evaluate([o[1] if o[0] in ("op", "const") else f"{o[0]}{o[1]}" for o in ops],
                               {**{f"slot{j}": x for j, x in enumerate(vals)}, **{f"step{j}": x for j, x in enumerate(res)}}))
    return res


def plant(idx, info, k, why):
    v = info["results"][k]
    vals = [x for _, x in info["slots"]]
    right = info["results"][-1]
    if v.denominator != 1 or v <= 1:
        return why.append(f"step {k}: result not a whole number above 1")
    if v in vals:
        return why.append(f"step {k}: result also a question number")
    rng = random.Random(1000 * idx + k)
    lo, hi = max(1, math.ceil(v * F(1, 10))), max(2, math.floor(v * F(1, 2)))
    for _ in range(200):
        p = v + rng.choice((-1, 1)) * rng.randint(lo, max(lo, hi))
        if p <= 0 or p == v:
            continue
        try:
            follow = replay_from(info["prog"], vals, k, p)[-1]
        except ZeroDivisionError:
            continue
        if follow.denominator == 1 and follow > 0 and follow != right:
            return dict(step=k, true=int(v), planted=int(p), follow=int(follow))
    why.append(f"step {k}: no planted value gives a whole, positive, different answer")


def main():
    items, skipped = [], {}
    for idx, line in enumerate(open(sys.argv[1])):
        d = json.loads(line)
        info = tw.analyse(d["question"], d["answer"])
        if not info or len(info["prog"]) < 3:
            continue
        why = []
        n = len(info["prog"])
        e, l = plant(idx, info, 0, why), plant(idx, info, n - 2, why)
        if not (e and l) or e["true"] == l["true"]:
            r = why[0] if why else "early and late results equal"
            skipped[r.split(": ", 1)[-1]] = skipped.get(r.split(": ", 1)[-1], 0) + 1
            continue
        items.append(dict(idx=idx, question=d["question"], answer=int(info["results"][-1]), steps=n, early=e, late=l))
    json.dump(items, open(sys.argv[2], "w"), indent=1)
    print(f"written {len(items)} items with 3+ steps; skipped: {skipped}")


main()
