"""Exploratory comparison: the pair-judging results on the original screenshots against the same pairs re-judged on
screens cropped to their interior (crop.py, judge_pairs.py --crop). Same scoring as analyse.py: per pair, the share of
judge votes for the factory (two judges, two orders; a tie counts half). Not one of the pre-registered tests.
Usage: python3 analyse_crop.py <stage dir>   -> <stage dir>/analysis-crop.md"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyse import JUDGES, CRIT, slug, mean, boot, signflip, sign_test, table


def votes(stage, prefix):
    out, raw = {}, []
    for j in JUDGES:
        f = stage / f"pairs-{prefix}{slug(j)}.jsonl"
        last = {}
        for line in f.open():
            r = json.loads(line)
            if "error" not in r:
                last[(r["brief"], r["rep"], r["view"], r["first"])] = r
        for (b, rep, view, first), r in last.items():
            raw.append(r)
            for c in CRIT:
                if c in r:
                    v = r[c]
                    out.setdefault((b, rep, view, c), []).append(0.5 if v == "tie" else (1.0 if (v == "1") == (first == "B") else 0.0))
    return out, raw


def main(stage):
    stage = Path(stage)
    V = {"original screenshots": votes(stage, ""), "cropped to the screen": votes(stage, "crop-")}
    pairs = sorted({(b, r) for (b, r, v, c) in V["original screenshots"][0]})
    md = ["# Exploratory re-score: cropped to the screen interior", "",
          "Same pairs, same judges, same prompt; only the images differ. Score per pair = share of the judge votes (two judges, "
          "two orders) that chose the factory's design; above 0.5 the factory wins the pair, below 0.5 the plain agent does. "
          "Not a pre-registered test.", ""]
    rows = []
    sc = {}
    for view, label in (("whole", "whole design"), ("looks", "looks only (first six screens)")):
        for name, (vt, _) in V.items():
            s = [mean(vt[(b, r, view, "overall")]) for b, r in pairs if (b, r, view, "overall") in vt]
            sc[(view, name)] = s
            w, l = sum(x > .5 for x in s), sum(x < .5 for x in s)
            d = [x - .5 for x in s]
            lo, hi = boot(d)
            rows.append([label, name, len(s), w, l, len(s) - w - l, f"{mean(s):.2f} ({lo + .5:.2f} to {hi + .5:.2f})", f"{signflip(d):.4f}", f"{sign_test(w, l):.4f}"])
    md += [table(["View", "Images", "Pairs", "Factory wins", "Plain wins", "Split", "Mean score (95% CI)", "p (sign-flip)", "Sign test p"], rows), ""]
    rows = []
    for c in CRIT:
        row = [c]
        for view in ("whole", "looks"):
            for name, (vt, _) in V.items():
                x = [mean(vt[(b, r, view, c)]) for b, r in pairs if (b, r, view, c) in vt]
                row.append(f"{mean(x):.2f}" if x else "-")
        rows.append(row)
    md += ["### By criterion (mean pair score; above 0.5 favours the factory)", "",
           table(["Criterion", "Whole: original", "Whole: cropped", "Looks: original", "Looks: cropped"], rows), ""]
    rows = []
    for name, (vt, raw) in V.items():
        for j in JUDGES:
            rr = [r for r in raw if r["judge"] == j]
            fv = {}
            for r in rr:
                fv.setdefault((r["brief"], r["rep"], r["view"]), {})[r["first"]] = r["overall"]
            same = sum(1 for k, d in fv.items() if len(d) == 2 and ((d["A"] == "1") != (d["B"] == "1")) ) / max(1, sum(1 for d in fv.values() if len(d) == 2))
            first = sum(r["overall"] == "1" for r in rr) / len(rr)
            rows.append([name, j, len(rr), f"{first:.0%}", f"{same:.0%}"])
    md += ["### The judges", "", "Chose the first design shown (50% = no position bias); same choice in both orders.", "",
           table(["Images", "Judge", "Calls", "Chose first design shown", "Same choice in both orders"], rows), ""]
    (stage / "analysis-crop.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main(sys.argv[1])
