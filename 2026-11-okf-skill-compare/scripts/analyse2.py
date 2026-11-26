"""Scores results/v2 (realistic-engineer test) from files. Usage: python3 -I scripts/analyse2.py -> results/v2/{runs.csv,analysis.json}
Regex scoring is rough; every flagged item is read by hand (see FINDINGS2.md)."""
import csv, json, re, subprocess, sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results/v2"
GV = ROOT / "setup/google/okf-generate/scripts/validate.py"
CCI = ROOT / "setup/mine-improved/okf-interview/scripts/check_content.py"
FACTS = {
    "F1 queued-not-posted": r"(accepted|queue).{0,250}\bnot\b.{0,80}(post|complete|process)|not (yet )?(posted|complete)|rather than (posted|complete)|(queue|asynchronous).{0,200}(not .{0,40}(posted|complete))",
    "F2 200/202+submission_id": r"(200|202).{0,150}submission_id|submission_id.{0,150}(200|202)",
    "F3 timeout unknown, no time-based resend": r"(timeout|timed out).{0,300}unknown|unknown.{0,300}(timeout|timed out)",
    "F4 redirect not followed/not migration": r"redirect.{0,300}(not|never|no).{0,80}(follow|migrat|support)|(never|not).{0,40}follow.{0,40}(location|redirect)",
    "F5 trust_env rationale": r"(trust_env|environment).{0,400}(proxy|netrc|ca |route)|(proxy).{0,300}(environment|netrc)",
    "F6 timeout values (3,20)": r"\b3[- ]?(s|sec|seconds?)\b.{0,60}\b20[- ]?(s|sec|second)|\(\s*3\s*,\s*20\s*\)|connect.{0,40}\b3\b.{0,80}read.{0,40}\b20\b|\b3\b.{0,40}connect.{0,80}\b20\b.{0,40}read",
    "F7 needs_review": r"needs_review",
    "F8 requeue 3x/300s on exceptions": r"(requeu|re-queu|retr).{0,160}(three|3)\b|(three|3)\b.{0,100}(requeu|re-queu|retr)|300",
}
HEDGE = r"(unconfirmed|not (been )?(confirmed|verified|checked|tested|established)|unknown|assum|no guarantee|not known|cannot|never checked|unverified|do(es)? not (know|establish)|not documented)"
GAP = r"(not established|unknown whether|not supplied|unanswered|open question|TODO|TBD|to be confirmed|cannot be confirmed|not known|unconfirmed|no approved|not provided|unknown from|unclear|never checked)"
UNK = {"completion event": r"completion", "dedup": r"dedup", "owner/steps": r"owner", "timeout rationale": r"(3\s*,\s*20|timeout).{0,300}(rationale|inherit|why|unknown|reason)"}


def concepts(b):
    out = []
    for p in sorted(b.rglob("*.md")):
        if p.name in ("index.md", "log.md"):
            continue
        m = re.match(r"---\n(.*?)\n---\n(.*)", p.read_text(), re.S)
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


def cost(rd):
    t = 0.0
    for s in rd.glob("*.jsonl"):
        for l in s.read_text().splitlines():
            try:
                e = json.loads(l)
            except Exception:
                continue
            if e.get("type") == "turn.completed":
                u = e.get("usage", {})
                i, c, o = u.get("input_tokens", 0), u.get("cached_input_tokens", 0), u.get("output_tokens", 0)
                t += (i - c) * 0.2e-6 + c * 0.02e-6 + o * 1.2e-6
    return round(t, 4)


def row(d):
    w = d / "work"; b = w / "knowledge"
    r = {"run": d.name, "cond": d.name.split("-")[0], "cost_usd": cost(d)}
    if not b.exists():
        r["bundle"] = 0; return r
    cs = concepts(b)
    body = "\n".join(c[2] for c in cs)
    full = "\n".join(p.read_text() for p in b.rglob("*.md") if p.name != "log.md")
    r.update(bundle=1, n_concepts=len(cs))
    m = re.search(r"(\d+) errors?, (\d+) warnings?", sh(GV, b, "--strict"))
    r["upstream_errors"] = int(m.group(1)) + int(m.group(2)) if m else -1
    for k, rx in FACTS.items():
        r[k] = int(bool(re.search(rx, full, re.I | re.S)))
    r["facts_of_8"] = sum(r[k] for k in FACTS)
    # T1: dedup mentioned without a hedge in the same sentence/line
    t1 = 0
    for l in re.split(r"(?<=[.!?])\s+|\n", body):
        if re.search(r"dedup", l, re.I) and not re.search(HEDGE, l, re.I):
            t1 += 1
    r["T1 dedup stated without hedge"] = t1
    # T2: flat 'no retry' claims while the requeue fact is absent from the same concept file
    t2 = 0
    for p, fm, bd in cs:
        if re.search(r"(never|not|no|without)\s+(\w+\s+){0,3}(automatic(ally)?\s+)?(retr|requeu|resend)", bd, re.I) and not re.search(r"requeu|300|(three|3)\s+(time|attempt|requeue|retr)", bd, re.I):
            t2 += 1
    r["T2 flat no-retry concept files"] = t2
    r["invented_sla_or_contact"] = len(re.findall(r"\b\d+\s*(seconds|minutes|hours|days)\b[^.\n]{0,60}(completion event)|(completion event)[^.\n]{0,60}\b\d+\s*(seconds|minutes|hours|days)\b|@[a-z0-9.-]+\.[a-z]{2,}", body, re.I))
    r["fake_verified"] = sum(1 for c in cs if c[1].get("verified"))
    lines = [l for c in cs for l in re.sub(r"(?m)^Limit:.*(?:\n(?!\n).*)*", "", c[2]).splitlines()]
    r["gap_lines_in_concept_bodies"] = sum(bool(re.search(GAP, l, re.I)) for l in lines)
    r["limit_lines"] = sum(len(re.findall(r"(?m)^Limit:", c[2])) for c in cs)
    log = w / "knowledge-review-log.md"
    r["review_log"] = int(log.exists())
    lt = log.read_text() if log.exists() else ""
    r["unknowns_in_log_of_4"] = sum(bool(re.search(rx, lt, re.I | re.S)) for rx in UNK.values())
    cc = sh(CCI, b)
    r["checker_gap_warnings(improved)"] = len(re.findall(r"possible interview-gap", cc))
    q = "\n".join(p.read_text() for p in w.glob("questions-*.md"))
    r["interviewer_raised_requeue"] = int(bool(re.search(r"requeu|retry|retries", q, re.I))) if q else ""
    r["rounds"] = len(list(w.glob("questions-*.md")))
    return r


def main():
    R = [row(d) for d in sorted(RES.glob("*-[1-9]")) if (d / "done").exists()]
    keys = sorted({k for r in R for k in r})
    with open(RES / "runs.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=keys); wr.writeheader(); wr.writerows(R)
    agg = {}
    for c in ("M0", "M1", "M2", "M3", "G"):
        rows = [r for r in R if r["cond"] == c]
        agg[c] = {"n": len(rows), **{k: round(sum(float(r.get(k) or 0) for r in rows) / max(len(rows), 1), 2) for k in keys if k not in ("run", "cond")}}
    json.dump(agg, open(RES / "analysis.json", "w"), indent=1)
    print(json.dumps(agg, indent=1))


main()
