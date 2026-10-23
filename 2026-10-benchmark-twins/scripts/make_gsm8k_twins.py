"""Builds GSM8K twins with answers recomputed exactly (README, "Items"). No language model is used.

For each GSM8K test item, the reference solution's calculator steps (<<expr=result>>) are replayed with exact fractions.
Every operand must be explained: a number written in digits in the question (a "slot", which the twins change), a number
word in the question, an earlier step's result, or a fixed constant (unit conversions). Items are skipped when that fails,
when a slot value occurs twice, or when an operand could be two things. The replay must reproduce every original result.

Twins (same item, four variants):
  orig     the original question
  names    first names swapped for others of the same list (female or male), so pronouns still agree; only for items
           with a first name on the lists (otherwise names and both are null)
  numbers  every slot given a new value: same number of digits, within 0.5x to 1.5x, same multiple of 10 or 5, same
           decimals, and the same order among the question's numbers (if a < b before, a < b after: no "16 of 12 chairs");
           kept only if every step keeps its sign (> 0 stays > 0), stays whole where the original was whole, and the
           answer changes but keeps its number of digits. Reference-solution errors in GSM8K are replayed as they are
  both     names and numbers together
Draws use random.Random(seed) per item (seed = 1 + item index), so the twins are reproducible.
Usage: python3 -I make_gsm8k_twins.py <gsm8k test.jsonl> <out.json> [n items, default all valid]
"""
import json, random, re, sys
from fractions import Fraction as F

CONST = {F(x) for x in (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 24, 30, 31, 52, 60, 100, 365, 1000, 0.5, 0.25)}
UNIT = {F(x) for x in (7, 10, 12, 24, 30, 31, 52, 60, 100, 365, 1000)}  # conversion constants that can hide behind a slot
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12, "twenty": 20, "thirty": 30, "fifty": 50, "hundred": 100, "dozen": 12, "half": F(1, 2),
         "twice": 2, "double": 2, "triple": 3, "thrice": 3, "quarter": F(1, 4), "percent": 100}
IMPLIED = {"half": 2, "halves": 2, "quarter": 4, "quarters": 4, "dozen": 12, "dozens": 12, "percent": 100, "pair": 2, "pairs": 2,
           "week": 7, "weeks": 7, "hour": 60, "hours": 60, "minute": 60, "minutes": 60, "year": 12, "years": 12, "day": 24, "days": 24}
FEMALE = "Janet Mary Linda Susan Karen Nancy Lisa Betty Sandra Ashley Emily Donna Michelle Carol Amanda Melissa Deborah Laura Rebecca Sharon Cynthia Kathleen Amy Angela Anna Brenda Emma Olivia Sophia Mia Chloe Grace Lily Hannah Zoe Ella Ava Isla Ruby Alice Julia Rosa Nina Tara Wendy Paula Gloria Diana Fiona Helen Irene Joan Kelly Lucy Megan Nora Paige Rachel Sara Tina Vera Yara Jenna Rita Carla Elena Maya Leah Molly Kayla Josie Sienna Erin Jade".split()
MALE = "James John Robert Michael William David Richard Joseph Thomas Charles Daniel Matthew Anthony Mark Paul Steven Andrew Kenneth Joshua Kevin Brian George Edward Ronald Timothy Jason Jeffrey Ryan Jacob Gary Eric Jonathan Stephen Larry Justin Scott Brandon Frank Gregory Samuel Peter Henry Jack Liam Noah Ethan Lucas Mason Logan Oliver Leo Max Sam Tom Ben Carl Dan Ian Joe Ken Luke Nick Omar Raj Tim Victor Wade Zack Hugo Felix Ivan Marco Owen Seth Theo Adam Colin Dean".split()
NUM = re.compile(r"(?<![\w.,])\$?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?![\w]|[.,]\d)")
STEP = re.compile(r"<<([^=<>]+)=([^<>]+)>>")


def val(s):
    return F(s.replace(",", "").replace("$", ""))


def fmt(x, like):
    """Formats new value x like the original token `like` (commas, decimals)."""
    dec = len(like.split(".")[1]) if "." in like else 0
    s = f"{float(x):.{dec}f}" if dec else str(int(x))
    if "," in like:
        s = f"{int(x):,}"
    return s


def tokens(expr):
    return re.findall(r"\d+(?:\.\d+)?|[-+*/()]|\S", expr.replace(",", "").replace("$", "").replace("x", "*").replace("%", "/100"))


def evaluate(toks, env):
    s = ""
    for t in toks:
        if t in env:
            s += f"F({env[t]!r})" if not isinstance(env[t], F) else f"F({env[t].numerator},{env[t].denominator})"
        elif re.fullmatch(r"\d+(?:\.\d+)?", t):
            s += f"F('{t}')"
        elif t in "+-*/()":
            s += t
        else:
            raise ValueError(t)
    return eval(s, {"F": F, "__builtins__": {}})


WHY = {}


def skip(reason):
    WHY[reason] = WHY.get(reason, 0) + 1
    return None


def analyse(q, a):
    if re.search(r"\d:\d|\d/\d|\d\s*(st|nd|rd|th)\b|%", q):
        return skip("time, fraction, ordinal or % in question")
    toks = [m.group(1) for m in NUM.finditer(q)]
    # one slot per distinct value: a value written twice is changed to the same new value everywhere, so the replay
    # stays exact whichever occurrence the solution used
    slots = []
    for t in toks:
        if val(t) not in [v for _, v in slots]:
            slots.append((t, val(t)))
    vals = [v for _, v in slots]
    if not slots:
        return skip("no number in digits")
    if F(2) in vals and re.search(r"\bboth\b", q, re.I):
        return skip("'both' with a 2 in the question")
    words = {F(v) for w, v in WORDS.items() if re.search(rf"\b{w}\b", q, re.I)} | \
            {F(v) for w, v in IMPLIED.items() if re.search(rf"\b{w}\b", q, re.I)}
    marked = STEP.sub("§", a.split("####")[0])  # an "=" followed by a calculator step (here §) is annotated
    if re.search(r"\d\s*[-+*/x×÷]\s*\(?\d[\d.,]*\)?\s*=\s*(?!\$?\s*§)", marked) or re.search(r"\b\d+[a-z]\b\s*=\s*(?!\$?\s*§)", marked):
        return skip("arithmetic outside the calculator steps")  # e.g. "60/15 = 4" in plain text, then <<4*4=16>>
    steps = STEP.findall(a)
    final = a.split("####")[-1].strip().replace(",", "")
    if not steps:
        return skip("no calculator steps")
    prog, results = [], []
    for expr, res in steps:
        toks = tokens(expr)
        ops = []
        for t in toks:
            if re.fullmatch(r"\d+(?:\.\d+)?", t):
                v = F(t)
                cands = [("slot", i) for i, x in enumerate(vals) if x == v] + [("step", i) for i, x in enumerate(results) if x == v]
                if cands and cands[0][0] == "slot" and (v in words or v in UNIT):  # e.g. a $12 price and 12 months a year
                    cands.append(("const", t))
                if len(cands) > 1:
                    return skip("operand could be two things")
                if cands:
                    ops.append(cands[0])
                elif v in words or v == 1:  # constants only when a word in the question implies them
                    ops.append(("const", t))
                else:
                    return skip("operand not explained")
            else:
                ops.append(("op", t))
        try:
            r = evaluate([o[1] if o[0] in ("op", "const") else f"{o[0]}{o[1]}" for o in ops],
                         {**{f"slot{i}": x for i, x in enumerate(vals)}, **{f"step{i}": x for i, x in enumerate(results)}})
            if r != val(res.strip().rstrip(".")):
                return skip("replay does not reproduce a step")
        except Exception:
            return skip("step not parseable")
        prog.append(ops); results.append(r)
    try:
        if results[-1] != F(final):
            return skip("last step is not the answer")
    except Exception:
        return skip("answer not parseable")
    used = [any(o == ("slot", i) for p in prog for o in p) for i in range(len(vals))]
    if not any(used):
        return skip("no question number used")
    return dict(slots=slots, used=used, prog=prog, results=results)


def replay(prog, vals):
    res = []
    for ops in prog:
        res.append(evaluate([o[1] if o[0] in ("op", "const") else f"{o[0]}{o[1]}" for o in ops],
                            {**{f"slot{i}": x for i, x in enumerate(vals)}, **{f"step{i}": x for i, x in enumerate(res)}}))
    return res


def new_value(tok, v, rng):
    dec = len(tok.split(".")[1]) if "." in tok else 0
    step = F(1, 10 ** dec)
    mult = 10 if (dec == 0 and v % 10 == 0 and v >= 10) else 5 if (dec == 0 and v % 5 == 0 and v >= 5) else 1
    lo, hi = max(step, v * F(1, 2)), v * F(3, 2)
    digits = len(str(int(v))) if dec == 0 else None
    for _ in range(50):
        x = F(rng.randint(int(lo / step), max(int(lo / step), int(hi / step)))) * step
        if mult > 1:
            x = (x // mult) * mult
        if x <= 0 or x == v or (dec == 0 and x == 1) or (digits and len(str(int(x))) != digits):  # never 1: "1 books"
            continue
        if dec and (x * 10 ** dec) % 10 == 0 and (v * 10 ** dec) % 10 != 0:  # 1.5 must not become "1.0"
            continue
        return x
    return None


def swap_names(q, rng):
    out, used = q, set(re.findall(r"\b[A-Z][a-z]+\b", q))
    for lst in (FEMALE, MALE):
        for n in sorted({w for w in used if w in lst}):
            pick = rng.choice([x for x in lst if x not in used])
            used.add(pick)
            out = re.sub(rf"\b{n}\b", pick, out)
    return out if out != q else None


def main():
    src, dst = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else None
    items, skipped = [], 0
    for idx, line in enumerate(open(src)):
        d = json.loads(line)
        info = analyse(d["question"], d["answer"])
        if not info:
            skipped += 1; continue
        rng = random.Random(1 + idx)
        names_q = swap_names(d["question"], rng)  # None when no listed first name: names and both are then absent
        twin = None
        for _ in range(200):
            nv = [new_value(t, v, rng) if u else v for (t, v), u in zip(info["slots"], info["used"])]
            if None in nv:
                continue
            try:
                res = replay(info["prog"], nv)
            except ZeroDivisionError:
                continue
            ok = all((r > 0 if o > 0 else r >= 0) and (r.denominator == 1 or o.denominator != 1) for r, o in zip(res, info["results"]))
            ans_o, ans_t = info["results"][-1], res[-1]
            same_size = len(str(abs(int(ans_t)))) == len(str(abs(int(ans_o))))
            vo = [v for _, v in info["slots"]]
            order = all((vo[i] < vo[j]) == (nv[i] < nv[j]) for i in range(len(vo)) for j in range(len(vo)) if i != j)
            if ok and order and ans_t != ans_o and ans_t.denominator == 1 and same_size:
                twin = (nv, res[-1]); break
        if not twin:
            skip("no valid twin in 200 draws"); skipped += 1; continue

        def apply(q, nv):
            new = {v: fmt(x, t) for (t, v), x in zip(info["slots"], nv)}
            return NUM.sub(lambda m: m.group(0).replace(m.group(1), new[val(m.group(1))]), q)
        num_q = apply(d["question"], twin[0]); both_q = apply(names_q, twin[0]) if names_q else None
        ans = int(info["results"][-1]) if info["results"][-1].denominator == 1 else float(info["results"][-1])
        items.append(dict(idx=idx, orig=d["question"], names=names_q, numbers=num_q, both=both_q,
                          answer_orig=ans, answer_twin=int(twin[1]), steps=len(info["prog"]), slots=len(info["slots"])))
    rng = random.Random(1)
    chosen = sorted(rng.sample(items, n), key=lambda x: x["idx"]) if n and n < len(items) else items
    json.dump(chosen, open(dst, "w"), indent=1)
    print(f"valid {len(items)} of {len(items) + skipped}; written {len(chosen)}")
    print("skipped:", dict(sorted(WHY.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
