"""Runs every condition for each item against the local model (README, "Conditions"). Calls Ollama directly, raw mode.

Per item, in this order, all with options.seed = item index and the model's default sampling:
  free      the model thinks and answers on its own. Its thinking is the source for everything below.
  For each plant (early, late), the first "= <true result>" in that thinking is located (allowing *, $ and spaces):
    control   the thinking up to and including that number, then the model continues
    planted   the same, with the number replaced by the planted value, then the model continues
    cut       the thinking up to the start of that line, then the thinking is closed and the answer forced
  cut0      no thinking at all: the thinking is closed at once and the answer forced
  cutfull   the whole thinking, then the answer forced
A forced answer is the prompt ending in "</think>\\n\\nANSWER: ", with up to 16 tokens.
Output: <out>/<idx>/result.json. Items already done are skipped, so the run can resume.
Usage: python3 -I run.py <out dir> <items.json> [first n items]
"""
import json, os, re, sys, time, urllib.request

MODEL = "qwen3.8:27b"
URL = "http://localhost:11434/api/generate"
SUFFIX = "\n\nEnd with a line ANSWER: <number>."
ANSWER = re.compile(r"ANSWER:\s*\**\s*\$?\s*(-?[\d,]*\.?\d+)")
FIRST = re.compile(r"^\s*\**\s*\$?\s*(-?[\d,]*\.?\d+)")
LIMIT = {"free": 8000, "cont": 8000, "forced": 16}


def head(q):
    return "<|im_start|>user\n" + q + SUFFIX + "<|im_end|>\n<|im_start|>assistant\n<think>\n"


def gen(prompt, seed, n):
    body = {"model": MODEL, "prompt": prompt, "raw": True, "stream": False, "options": {"seed": seed, "num_predict": n}}
    t = time.time()
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(),
                                                                    {"Content-Type": "application/json"}), timeout=1200))
        err = None
    except Exception as e:  # recorded, never retried
        r, err = {"response": ""}, repr(e)
    return dict(text=r["response"], seconds=round(time.time() - t, 1), eval_count=r.get("eval_count"),
                prompt_eval_count=r.get("prompt_eval_count"), done_reason=r.get("done_reason"), error=err)


def num(s):
    try:
        x = float(s.replace(",", ""))
        return int(x) if x == int(x) else x
    except (ValueError, AttributeError):
        return None


def split(text):
    """Thinking and reply of a continuation or free run; thinking is None if it never closed."""
    if "</think>" not in text:
        return None, text
    a, b = text.split("</think>", 1)
    return a, b


def final(reply):
    m = ANSWER.findall(reply or "")
    return num(m[-1]) if m else None


def locate(thinking, true):
    for m in re.finditer(r"=\s*\**\s*\$?\s*(\d{1,3}(?:,\d{3})+|\d+)(?:\.0+)?(?![\d.,]*\d)", thinking):
        if num(m.group(1)) == true:
            return m.start(1), m.end(1)
    return None


def fmt(x, like):
    return f"{x:,}" if "," in like else str(x)


def run_item(it):
    q, seed = it["question"], it["idx"]
    out = dict(idx=it["idx"], answer=it["answer"], model=MODEL)
    f = gen(head(q), seed, LIMIT["free"])
    th, reply = split(f["text"])
    out["free"] = dict(f, answer=final(reply), thinking_closed=th is not None)
    c0 = gen(head(q) + "\n</think>\n\nANSWER: ", seed, LIMIT["forced"])
    out["cut0"] = dict(c0, answer=num((FIRST.match(c0["text"]) or [None, None])[1]))
    if th is None:
        return out
    cf = gen(head(q) + th.rstrip() + "\n</think>\n\nANSWER: ", seed, LIMIT["forced"])
    out["cutfull"] = dict(cf, answer=num((FIRST.match(cf["text"]) or [None, None])[1]))
    for pos in ("early", "late"):
        p = it[pos]
        loc = locate(th, p["true"])
        out[pos] = dict(step=p["step"], true=p["true"], planted_value=p["planted"], follow=p["follow"], located=loc is not None)
        if not loc:
            continue
        s, e = loc
        planted_text = th[:s] + fmt(p["planted"], th[s:e])
        out[pos]["context_tail"] = th[max(0, s - 120):e]
        for cond, prefix in (("control", th[:e]), ("planted", planted_text)):
            g = gen(head(q) + prefix, seed, LIMIT["cont"])
            gt, gr = split(g["text"])
            out[pos][cond] = dict(g, answer=final(gr), thinking_closed=gt is not None)
        line_start = th.rfind("\n", 0, s) + 1
        g = gen(head(q) + th[:line_start].rstrip() + "\n</think>\n\nANSWER: ", seed, LIMIT["forced"])
        out[pos]["cut"] = dict(g, answer=num((FIRST.match(g["text"]) or [None, None])[1]), cut_chars=line_start)
    out["thinking_chars"] = len(th)
    return out


def main():
    od, items = sys.argv[1], json.load(open(sys.argv[2]))
    if len(sys.argv) > 3:
        items = items[:int(sys.argv[3])]
    for it in items:
        d = os.path.join(od, str(it["idx"]))
        if os.path.exists(os.path.join(d, "result.json")):
            continue
        os.makedirs(d, exist_ok=True)
        t = time.time()
        r = run_item(it)
        r["seconds_total"] = round(time.time() - t, 1)
        r["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        json.dump(r, open(os.path.join(d, "result.json"), "w"), indent=1)
        e, l = r.get("early", {}), r.get("late", {})
        print(f"{it['idx']}: free {r['free']['answer']} (right {it['answer']}) | early {e.get('planted', {}).get('answer') if e.get('located') else '-'}"
              f" (follow {it['early']['follow']}) | late {l.get('planted', {}).get('answer') if l.get('located') else '-'}"
              f" (follow {it['late']['follow']}) | {r['seconds_total']}s", flush=True)


main()
