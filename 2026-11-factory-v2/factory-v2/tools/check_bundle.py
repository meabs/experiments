#!/usr/bin/env python3
"""Checks the factory itself. Usage: python3 tools/check_bundle.py   (run from anywhere)

- every skills/<name>/SKILL.md has name and description frontmatter, the name matches its folder, and the skill is
  linked from okf/index.md;
- every .md under okf/ (except index.md) is linked from okf/index.md or from an industry index;
- every markdown link in AGENTS.md, CLAUDE.md, okf/ and skills/ resolves to a file (links starting with / are relative
  to okf/), and every backticked okf/... or tools/... path in a skill exists.
Exit code 1 on any problem.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OKF = os.path.join(ROOT, "okf")
problems = []


def links(path):
    text = open(path, encoding="utf-8").read()
    out = []
    for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
        if re.match(r"[a-z]+:", target):
            continue
        dest = os.path.join(OKF, target.lstrip("/")) if target.startswith("/") else os.path.join(os.path.dirname(path), target)
        out.append(os.path.normpath(dest))
    return text, out


md = [os.path.join(ROOT, n) for n in ("AGENTS.md", "CLAUDE.md", "README.md") if os.path.exists(os.path.join(ROOT, n))]
for base in ("okf", "skills"):
    for r, _, ns in os.walk(os.path.join(ROOT, base)):
        md += [os.path.join(r, n) for n in ns if n.endswith(".md")]

linked = {}
for p in md:
    text, ls = links(p)
    linked[p] = set(ls)
    for dest in ls:
        if not os.path.exists(dest):
            problems.append(f"{os.path.relpath(p, ROOT)}: broken link to {os.path.relpath(dest, ROOT)}")
    for ref in re.findall(r"`((?:okf|tools|skills)/[\w./-]+\.(?:md|py))`", text):
        if not os.path.exists(os.path.join(ROOT, ref)):
            problems.append(f"{os.path.relpath(p, ROOT)}: names missing file {ref}")

index = os.path.join(OKF, "index.md")
from_index = set(linked[index])
for p in list(from_index):
    if os.path.basename(p) == "index.md" and p in linked:
        from_index |= linked[p]

for name in sorted(os.listdir(os.path.join(ROOT, "skills"))):
    p = os.path.join(ROOT, "skills", name, "SKILL.md")
    if not os.path.exists(p):
        problems.append(f"skills/{name}: no SKILL.md")
        continue
    head = open(p, encoding="utf-8").read().split("---")
    fm = head[1] if len(head) > 2 else ""
    m = re.search(r"^name:\s*(.+)$", fm, re.M)
    if not m or m.group(1).strip() != name:
        problems.append(f"skills/{name}/SKILL.md: frontmatter name must be '{name}'")
    if not re.search(r"^description:\s*\S", fm, re.M):
        problems.append(f"skills/{name}/SKILL.md: no description")
    if p not in from_index:
        problems.append(f"skills/{name} is not listed in okf/index.md")

for p in md:
    if p.startswith(OKF) and p != index and p not in from_index:
        problems.append(f"{os.path.relpath(p, ROOT)} is not listed in okf/index.md (or an index it links to)")
    if p.startswith(OKF) and p != index and not open(p, encoding="utf-8").read().startswith("---"):
        problems.append(f"{os.path.relpath(p, ROOT)} has no frontmatter")

print("\n".join(problems) if problems else f"ok: {len(md)} files, {len(os.listdir(os.path.join(ROOT, 'skills')))} skills")
sys.exit(1 if problems else 0)
