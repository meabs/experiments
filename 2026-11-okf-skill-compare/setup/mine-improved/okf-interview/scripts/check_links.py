#!/usr/bin/env python3
"""Check an OKF bundle's navigation, which the upstream validator does not cover.

Reports (exit 1 if any):
  - a Markdown link in any .md file whose relative target does not exist;
  - a concept that its directory's index.md does not link to (orphan);
  - a directory without an index.md.
Standard library only.  Usage: python3 -I check_links.py <bundle-root>
"""
import re
import sys
from pathlib import Path

LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def targets(md: Path):
    text = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.S)
    for m in LINK.finditer(text):
        t = m.group(1).split("#")[0]
        if t and not re.match(r"^[a-z][a-z0-9+.-]*:", t, re.I):
            yield t


def main(root: Path) -> int:
    problems = []
    files = sorted(root.rglob("*.md"))
    for md in files:
        for t in targets(md):
            dest = (root / t.lstrip("/")) if t.startswith("/") else (md.parent / t)
            if not dest.resolve().exists():
                problems.append(f"{md.relative_to(root)}: broken link -> {t}")
    for d in sorted({p.parent for p in files} | {root}):
        idx = d / "index.md"
        if not idx.exists():
            problems.append(f"{d.relative_to(root) if d != root else '.'}: no index.md")
            continue
        linked = {(idx.parent / t).resolve() for t in targets(idx)}
        for md in sorted(d.glob("*.md")):
            if md.name not in ("index.md", "log.md") and md.resolve() not in linked:
                problems.append(f"{md.relative_to(root)}: concept not linked from {idx.relative_to(root)}")
    for p in problems:
        print(p)
    print(f"{len(files)} files checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_dir():
        sys.exit("usage: check_links.py <bundle-root>")
    sys.exit(main(Path(sys.argv[1])))
