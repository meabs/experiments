"""Scores results/main from files. Usage: python3 -I scripts/analyse.py   (writes results/main/{runs.csv,analysis.json}).
Write side: validators, required facts, gap text in the bundle, gaps recorded elsewhere, invented claims, fake verification.
Read side: answers.json against a key written before the runs. Regexes are rough; flagged items are read by hand (see FINDINGS.md)."""
import csv, json, re, subprocess, sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results/main"
GV = ROOT / "setup/google/okf-generate/scripts/validate.py"
CL = ROOT / "setup/mine-okf-interview/scripts/check_links.py"
CC = ROOT / "setup/mine-okf-interview/scripts/check_content.py"
FACTS = {  # present anywhere in the bundle (all concept text, case-insensitive)
    "queued-not-posted": r"(queue|asynchronous).{0,200}(not .{0,40}(posted|complete)|rather than)|(not .{0,60}posted).{0,200}(queue|async)",
    "200/202+submission_id": r"(200|202).{0,150}submission_id|submission_id.{0,150}(200|202)",
    "timeout=unknown,no time replay": r"(timeout|timed out).{0,300}(unknown)|(unknown).{0,300}(timeout)",
    "redirect not followed/not migration": r"redirect.{0,300}(not|never|no).{0,80}(follow|migrat|support)|(never|not).{0,40}follow.{0,40}(location|redirect)",
    "trust_env rationale": r"(trust_env|environment).{0,400}(proxy|netrc|ca |route)|(proxy).{0,300}(environment|netrc)",
    "timeout (3,20)": r"\(?3\s*,\s*20\)?|3 seconds.{0,40}20|connect.{0,30}3.{0,60}read.{0,30}20",
}
GAP = r"(not established|unknown whether|not supplied|unanswered|open question|TODO|TBD|to be confirmed|cannot be confirmed|not known|not part of the established|is unknown|are unknown|was not provided|not provided|unclear)"
INVENT = {
    "vendor-dedup-asserted": r"(vendor|service|partner)[^.\n]{0,60}\b(does|do|will|can)\s+(not\s+)?dedup|(is|are)\s+(idempotent|deduplicated)|safe to (re)?send",
    "sla-number": r"\b\d+\s*(seconds|minutes|hours|days)\b[^.\n]{0,60}(completion|event)|(completion|event)[^.\n]{0,60}\b\d+\s*(seconds|minutes|hours|days)\b",
    "named-owner/contact": r"@[a-z0-9.-]+\.[a-z]{2,}|\bcontact (is|at)\b",
    "timeout-rationale": r"(3|20)[^.\n]{0,40}(chosen|selected|picked|set|designed)[^.\n]{0,30}(because|to |so )",
}
NOTCOV = {"Q6": r"completion|event", "Q7": r"dedup", "Q8": r"owner", "Q9": r"timeout|3|20"}
KEY = {"Q1": r"queue|async", "Q2": r"(200.*202|202.*200).*submission_id|submission_id.*(200|202)", "Q3": r"\bno\b|not|never|unknown",
       "Q4": r"\bno\b|not|never", "Q5": r"(worker|direct|identity|route|silently|netrc)"}


def concepts(b):
    out = []
    for p in sorted(b.rglob("*.md")):
        if p.name in ("index.md", "log.md"):
            continue
        t = p.read_text()
        m = re.match(r"---\n(.*?)\n---\n(.*)", t, re.S)
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except Exception:
            fm = {}
        if isinstance(fm, dict) and fm.get("type"):
            out.append((p, fm, m.group(2)))
    return out


def sh(*a):
    r = subprocess.run([sys.executable, "-I", *map(str, a)], capture_output=True, text=True)
    return r.stdout + r.stderr


def write_row(d):
    w = d / "work"
    b = w / "knowledge"
    row = {"run": d.name, "cond": d.name.split("-")[1], "rep": d.name.split("-")[2]}
    if not b.exists():
        row["bundle"] = 0
        return row
    cs = concepts(b)
    body = "\n".join(c[2] for c in cs)
    full = "\n".join(p.read_text() for p in b.rglob("*.md") if p.name not in ("log.md",))
    row.update(bundle=1, n_concepts=len(cs))
    v = sh(GV, b, "--strict")
    m = re.search(r"(\d+) errors?, (\d+) warnings?", v)
    row["upstream_errors"], row["upstream_warnings"] = (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
    row["links_problems"] = int(re.search(r"(\d+) problem", sh(CL, b)).group(1)) if re.search(r"(\d+) problem", sh(CL, b)) else -1
    for k, rx in FACTS.items():
        row["fact:" + k] = int(bool(re.search(rx, full, re.I | re.S)))
    row["facts_present"] = sum(row["fact:" + k] for k in FACTS)
    # gap text inside concept bodies, excluding a "Limit:" sentence (the skill's allowed form)
    lines = [l for c in cs for l in c[2].splitlines() if not re.match(r"\s*Limit:", l)]
    row["gap_text_lines_in_concepts"] = sum(bool(re.search(GAP, l, re.I)) for l in lines)
    for k, rx in INVENT.items():
        row["invent:" + k] = len(re.findall(rx, body, re.I))
    row["invented_flags"] = sum(row["invent:" + k] for k in INVENT)
    row["fake_verified"] = sum(1 for c in cs if c[1].get("verified"))
    row["has_human_actor"] = int(bool(re.search(r"human:", full)))
    outside = "\n".join(p.read_text() for p in w.rglob("*.md") if b not in p.parents and p.name != "notes.md")
    topics = {"completion event": r"completion", "dedup": r"dedup", "owner/steps": r"owner", "timeout rationale": r"(3\s*,\s*20|timeout).{0,200}(rationale|inherit|why|unknown)"}
    row["unknowns_recorded_outside_bundle"] = sum(bool(re.search(rx, outside, re.I | re.S)) for rx in topics.values())
    row["unknowns_recorded_anywhere"] = sum(bool(re.search(rx, outside + "\n" + full, re.I | re.S)) for rx in topics.values())
    s = d / "session.jsonl"
    row["cost_usd"] = cost(s)
    return row


def cost(s):
    i = c = o = 0
    if s.exists():
        for l in s.read_text().splitlines():
            try:
                e = json.loads(l)
            except Exception:
                continue
            if e.get("type") == "turn.completed":
                u = e.get("usage", {})
                i += u.get("input_tokens", 0); c += u.get("cached_input_tokens", 0); o += u.get("output_tokens", 0)
    return round((i - c) * 0.2e-6 + c * 0.02e-6 + o * 1.2e-6, 4)


def read_row(d):
    n = d.name.split("-")
    row = {"run": d.name, "cond": n[1], "rep": n[2], "reader": n[3], "cost_usd": cost(d / "session.jsonl")}
    try:
        a = json.load(open(d / "work/answers.json"))
    except Exception:
        row["answers"] = 0
        return row
    row["answers"] = 1
    ok_ans = ok_not = 0
    for q, rx in KEY.items():
        x = a.get(q, {})
        ok_ans += int(str(x.get("covered_by_bundle", "")).lower().startswith("y") and bool(re.search(rx, str(x.get("answer", "")), re.I | re.S)))
    for q in NOTCOV:
        x = a.get(q, {})
        ok_not += int(str(x.get("covered_by_bundle", "")).lower().startswith("n"))
    row["answerable_correct_of5"], row["unanswerable_declined_of4"] = ok_ans, ok_not
    row["trust_reported"] = sum(bool(re.search(r"unverified|machine-confirmed|human-reviewed|draft", str(a.get(q, {}).get("trust", "")), re.I)) for q in a)
    return row


def main():
    W = [write_row(d) for d in sorted(RES.glob("write-*")) if (d / "done").exists()]
    R = [read_row(d) for d in sorted(RES.glob("read-*")) if (d / "done").exists()]
    keys = lambda rows: sorted({k for r in rows for k in r})
    for name, rows in (("write", W), ("read", R)):
        with open(RES / f"{name}.csv", "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=keys(rows)); wr.writeheader(); wr.writerows(rows)
    agg = {"write": {}, "read": {}}
    for cond in "MG":
        rows = [r for r in W if r["cond"] == cond]
        nums = [k for k in keys(rows) if k not in ("run", "cond", "rep")]
        agg["write"][cond] = {"n": len(rows), **{k: round(sum(r.get(k, 0) for r in rows) / max(len(rows), 1), 2) for k in nums}}
        for rd in "PK":
            rr = [r for r in R if r["cond"] == cond and r["reader"] == rd]
            agg["read"][f"{cond}/{rd}"] = {"n": len(rr), **{k: round(sum(r.get(k, 0) for r in rr) / max(len(rr), 1), 2) for k in ("answers", "answerable_correct_of5", "unanswerable_declined_of4", "trust_reported", "cost_usd")}}
    json.dump(agg, open(RES / "analysis.json", "w"), indent=1)
    print(json.dumps(agg, indent=1))


main()
