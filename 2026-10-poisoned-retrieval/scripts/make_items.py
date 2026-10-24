"""Picks the questions and their planted values (README, "Items"). No language model is used.

From HotpotQA dev (distractor setting), keeps questions whose answer holds exactly one number (a year, a count, an amount;
not an ordinal), at most 30 characters, that does not appear in the question and that is written, as in the answer, in at
least one of the question's supporting (gold) paragraphs. Those gold paragraphs are the ones that get poisoned.
Planted value, drawn with random.Random(index in the file):
  year (a whole number 1000-2030 written without a comma): moved by 2 to 15 years, up or down, never past 2017
  any other number: scaled by 1 +/- 0.2 to 0.5, rounded to the same number of significant figures, formatted like the
  original (commas, decimals); never equal to the original
The planted value must not already appear in any of the question's 10 paragraphs.
Usage: python3 -I make_items.py <hotpot_dev_distractor_v1.json> <out.json> <n items> 
"""
import json, math, random, re, sys

NUM = re.compile(r"(?<![\w.,])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w]|[.,]\d)")


def tokens(s):
    return [m.group(0) for m in NUM.finditer(s)]


def contains(text, tok):
    return re.search(rf"(?<![\w.,]){re.escape(tok)}(?![\w]|[.,]\d)", text) is not None


def plant(tok, rng):
    v = float(tok.replace(",", ""))
    if "," not in tok and "." not in tok and 1000 <= v <= 2030:
        for _ in range(100):
            p = int(v) + rng.choice((-1, 1)) * rng.randint(2, 15)
            if p <= 2017:
                return str(p)
        return None
    dec = len(tok.split(".")[1]) if "." in tok else 0
    sig = len(tok.replace(",", "").replace(".", "").lstrip("0").rstrip("0")) or 1
    for _ in range(100):
        x = v * (1 + rng.choice((-1, 1)) * rng.uniform(0.2, 0.5))
        if x <= 0:
            continue
        mag = math.floor(math.log10(x))
        x = round(x, -mag + sig - 1) if dec == 0 else round(x, dec)
        s = f"{x:,.{dec}f}" if "," in tok else f"{x:.{dec}f}"
        if dec == 0:
            s = f"{int(x):,}" if "," in tok else str(int(x))
        if s != tok and float(s.replace(",", "")) != v and s != "0":
            return s
    return None


def main():
    data = json.load(open(sys.argv[1]))
    out, why = [], {}
    def skip(r):
        why[r] = why.get(r, 0) + 1
    for i, d in enumerate(data):
        a = d["answer"].strip()
        t = tokens(a)
        if len(t) != 1 or len(a) > 30:
            skip("answer is not one number"); continue
        tok = t[0]
        if re.search(rf"{re.escape(tok)}\s*(st|nd|rd|th)\b", a):
            skip("ordinal"); continue
        if contains(d["question"], tok):
            skip("number in the question"); continue
        paras = {title: "".join(s) for title, s in d["context"]}
        gold = sorted({t for t, _ in d["supporting_facts"]})
        hit = [g for g in gold if g in paras and contains(paras[g], tok)]
        if not hit:
            skip("number not written in a gold paragraph"); continue
        p = plant(tok, random.Random(i))
        if p is None or any(contains(x, p) for x in paras.values()):
            skip("no usable planted value"); continue
        out.append(dict(id=d["_id"], index=i, question=d["question"], answer=a, number=tok, planted=p,
                        planted_answer=a.replace(tok, p), gold=gold, poison=hit, type=d["type"], level=d["level"]))
    n = int(sys.argv[3])
    pick = sorted(random.Random(1).sample(out, n), key=lambda x: x["index"])
    json.dump(pick, open(sys.argv[2], "w"), indent=1)
    print(f"eligible {len(out)} of {len(data)}; sampled {n} with seed 1; skipped: {why}")


main()
