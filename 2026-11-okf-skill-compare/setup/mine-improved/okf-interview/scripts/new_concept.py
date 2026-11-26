#!/usr/bin/env python3
"""Scaffold one interview-derived OKF concept with correct frontmatter and matching footnotes.

It fills the real current timestamp and the source entries; you write the body.  It never marks content verified.
Standard library only.

Usage:
  python3 -I new_concept.py <bundle-root>/<dir>/<name>.md --type Decision --title "..." --description "..." \
      --interview "Engineering interview about X on 2026-01-01; no recording retained" \
      --code "Repo revision <sha>, file/symbol" --by "process:okf-interview-author" [--synthetic] [--tag t ...]
"""
import argparse
import datetime
import sys
from pathlib import Path


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    a = argparse.ArgumentParser()
    a.add_argument("path")
    a.add_argument("--type", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--description", required=True)
    a.add_argument("--interview", required=True, help="truthful description of the interview scope (no invented URL or transcript)")
    a.add_argument("--code", required=True, help="repository revision and file/symbol evidence")
    a.add_argument("--by", required=True, help="real producer, e.g. 'process:okf-interview-author'")
    a.add_argument("--tag", action="append", default=[])
    a.add_argument("--synthetic", action="store_true", help="label as synthetic scenario knowledge")
    a.add_argument("--force", action="store_true")
    a.add_argument("--index-note", help="also append a link to the directory index.md with this one-line description")
    a = a.parse_args()
    p = Path(a.path)
    if p.suffix != ".md" or p.name in ("index.md", "log.md"):
        sys.exit("path must be a concept .md file (not index.md or log.md)")
    if p.exists() and not a.force:
        sys.exit(f"{p} exists; use --force to overwrite")
    now = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    fm = ["---", f"type: {a.type}", f"title: {q(a.title)}", f"description: {q(a.description)}"]
    if a.tag:
        fm.append("tags: [" + ", ".join(a.tag) + "]")
    fm += ["status: draft"]
    if a.synthetic:
        fm.append("x-okf-interview-synthetic: true")
    fm += ["sources:", "  - id: engineer", f"    resource: {q(a.interview)}", f"    title: {q('Engineer interview')}",
           "  - id: code", f"    resource: {q(a.code)}", f"    title: {q('Code evidence')}",
           "generated:", f"  by: {q(a.by)}", f"  at: {q(now)}", "---", ""]
    body = ["**Synthetic scenario knowledge; complete, unreviewed draft.**", ""] if a.synthetic else []
    body += ["<Lead with the actionable fact and its scope. Cite interview claims with [^engineer] and code facts with [^code].>", "",
             "[^engineer]: <Interview topic and date>", "[^code]: <Code evidence>", ""]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(fm + body), encoding="utf-8")
    if a.index_note:
        idx = p.parent / "index.md"
        head = "" if idx.exists() else "# " + p.parent.name.replace("-", " ").title() + "\n\n"
        with idx.open("a", encoding="utf-8") as f:
            f.write(head + f"- [{a.title}]({p.name}): {a.index_note}\n")
    print(f"wrote {p}; replace the placeholder body, add it to the directory index.md, then run check_links.py and validate.py")


if __name__ == "__main__":
    main()
