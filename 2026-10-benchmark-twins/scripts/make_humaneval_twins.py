"""Builds HumanEval twins (README, "Items"). No language model is used.

Twins (same item, two variants):
  orig     the original prompt (signature and docstring)
  renamed  the function renamed to a neutral name (`solution`) everywhere in the prompt, its docstring examples included,
           and in the tests where they name it. The behaviour asked for, the docstring and the tests are otherwise unchanged
Each twin is checked: the canonical solution, renamed the same way, must pass the renamed tests, and the original must pass
the original tests, both inside the same sandbox as the graded answers.
Sample: the run uses 80 of the items, random.Random(1).sample, written to <out>-sample.json (README, "Size and time").
Usage: python3 -I make_humaneval_twins.py <HumanEval.jsonl.gz> <out.json>
"""
import gzip, json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from grade_code import run_tests  # noqa: E402

NEW = "solution"


def rename(text, old):
    return re.sub(rf"\b{re.escape(old)}\b", NEW, text)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    rows = [json.loads(line) for line in gzip.open(src, "rt")]
    out, bad = [], []
    for i, r in enumerate(rows):
        ep = r["entry_point"]
        if re.search(rf"\b{NEW}\b", r["prompt"] + r["test"]):
            bad.append((r["task_id"], "name already used")); continue
        it = dict(idx=i, task_id=r["task_id"], entry_orig=ep, entry_renamed=NEW, orig=r["prompt"], renamed=rename(r["prompt"], ep),
                  test_orig=r["test"], test_renamed=rename(r["test"], ep))
        ok_o = run_tests(r["prompt"] + r["canonical_solution"], it["test_orig"], ep)[0]
        ok_r = run_tests(it["renamed"] + rename(r["canonical_solution"], ep), it["test_renamed"], NEW)[0]
        if not (ok_o and ok_r):
            bad.append((r["task_id"], f"canonical fails: orig {ok_o}, renamed {ok_r}")); continue
        out.append(it)
    json.dump(out, open(dst, "w"), indent=1)
    sample = sorted(random.Random(1).sample(out, 80), key=lambda it: it["idx"])
    json.dump(sample, open(dst.replace(".json", "-sample.json"), "w"), indent=1)
    print(f"written {len(out)} of {len(rows)}; left out: {bad}")


main()
