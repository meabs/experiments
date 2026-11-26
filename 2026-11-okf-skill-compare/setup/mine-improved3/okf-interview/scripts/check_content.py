#!/usr/bin/env python3
"""Mechanical content checks for interview-derived OKF concepts (complements validate.py and check_links.py).

Errors (exit 1):
  - leftover scaffold placeholders or TODO/TBD/FIXME markers;
  - a footnote reference with no definition, or a definition never referenced;
  - raw interview dialogue lines (Q:/A: style) in a concept body;
  - with --log FILE: a review item ID cited in a concept (R01, K03, ...) that is not a heading/ID in the log.
Warnings (printed, exit 0): phrases that usually mean interview-gap commentary leaked into a concept
(ignored inside quotation marks, backticks and a paragraph that starts with 'Limit:').
Passing does not show the content is true or complete.  Standard library only.
Usage: python3 -I check_content.py <bundle-root> [--log knowledge-review-log.md]
"""
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"<Lead with|<Interview topic|<Code evidence|<Specific decision|\bTODO\b|\bTBD\b|\bFIXME\b")
DIALOGUE = re.compile(r"^\s*(?:Q\d*|A\d*|Engineer|Interviewer)\s*[:)]", re.M)
GAP = re.compile(r"not established|was not supplied|were not supplied|to be confirmed|needs? clarification|unanswered|open question|not yet known|unconfirmed|no approved|not provided|unknown from", re.I)
ITEM = re.compile(r"review items?\s+([A-Z]\d{2,3}(?:\s*(?:,|and)\s*[A-Z]\d{2,3})*)", re.I)
ID = re.compile(r"[A-Z]\d{2,3}")


def body(text):
    return re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S)


def main(root, log):
    errs, warns = [], []
    ids = set(ID.findall(log.read_text(encoding="utf-8"))) if log else None
    for md in sorted(root.rglob("*.md")):
        if md.name in ("index.md", "log.md"):
            continue
        rel = md.relative_to(root)
        b = body(md.read_text(encoding="utf-8"))
        prose = re.sub(r"```.*?```", "", b, flags=re.S)
        if PLACEHOLDER.search(prose):
            errs.append(f"{rel}: placeholder or TODO marker left in body")
        refs = set(re.findall(r"\[\^([^\]]+)\](?!:)", prose))
        defs = set(re.findall(r"^\[\^([^\]]+)\]:\s*\S", prose, flags=re.M))
        for r in sorted(refs - defs):
            errs.append(f"{rel}: footnote [^{r}] is used but not defined")
        for r in sorted(defs - refs):
            warns.append(f"{rel}: footnote [^{r}] is defined but never used (the OKF spec allows it; the skill prefers every definition cited)")
        if DIALOGUE.search(prose):
            errs.append(f"{rel}: raw interview dialogue in concept body (keep it in evidence outside the bundle)")
        if ids is not None:
            for m in ITEM.finditer(prose):
                for i in ID.findall(m.group(1).upper()):
                    if i not in ids:
                        errs.append(f"{rel}: cites review item {i}, not found in {log.name}")
        scan = re.sub(r"(?m)^Limit:.*(?:\n(?!\n).*)*", "", prose)      # a scoped Limit paragraph is the sanctioned place
        scan = re.sub(r"`[^`]*`|\"[^\"]*\"|\u201c[^\u201d]*\u201d", "", scan)  # phrases quoted as examples are not commentary
        for m in GAP.finditer(scan):
            warns.append(f"{rel}: possible interview-gap commentary: \"{m.group(0)}\" (move to the review log, or keep only as a scoped 'Limit:' sentence)")
    for w in warns:
        print("warning:", w)
    for e in errs:
        print("error:", e)
    print(f"{len(errs)} error(s), {len(warns)} warning(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    log = None
    if "--log" in a:
        i = a.index("--log")
        log = Path(a[i + 1]); del a[i:i + 2]
    if len(a) != 1 or not Path(a[0]).is_dir() or (log and not log.is_file()):
        sys.exit("usage: check_content.py <bundle-root> [--log review-log.md]")
    sys.exit(main(Path(a[0]), log))
