#!/usr/bin/env python3
"""Quick structural checks on a built prototype. Usage: python3 tools/lint_prototype.py <folder or .html file>

Reads every .html file (and linked or inline CSS) without running it. Reports problems that are cheap to find from
the source. It does not replace the accessibility review: it cannot see rendered contrast, focus order or behaviour.

Checks: html lang; title; viewport (present, zoom not disabled); one h1 per screen section or page; heading levels
not skipped; images have alt; inputs, selects and textareas have a label (for=, wrapping label, aria-label or
aria-labelledby); buttons and links have a name; no click handlers on div or span; no positive tabindex; no
"outline: none" without a :focus-visible rule; no external network resources; no placeholder text ("lorem ipsum");
text sizes under 12px; contrast of --text / --text-muted / --on-primary style token pairs when they can be paired.
Exit code 1 if there are findings.
"""
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contrast import ratio  # noqa: E402

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.findings, self.stack, self.labels_for, self.ids = [], [], set(), set()
        self.controls, self.headings, self.css, self.title = [], [], [], ""
        self.lang = self.viewport = None
        self.in_style = self.in_title = False
        self.open_named = []  # buttons and links being read: [tag, attrs, text, line]
        self.label_depth = 0
        self.section_h1 = {}
        self.text = []

    def add(self, line, msg):
        self.findings.append((line, msg))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        line = self.getpos()[0]
        if tag not in VOID:
            self.stack.append((tag, a))
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self.in_title = True
        if tag == "style":
            self.in_style = True
        if tag == "meta" and a.get("name", "").lower() == "viewport":
            self.viewport = a.get("content", "")
        if tag == "label":
            self.label_depth += 1
            if a.get("for"):
                self.labels_for.add(a["for"])
        if tag in ("input", "select", "textarea") and a.get("type") not in ("hidden", "submit", "button", "reset", "image"):
            self.controls.append((line, tag, a, self.label_depth > 0))
        if tag == "input" and a.get("type") in ("submit", "button", "reset") and not (a.get("value") or a.get("aria-label")):
            self.add(line, "input button has no value or aria-label")
        if tag == "img" and "alt" not in a:
            self.add(line, "img has no alt attribute (use alt=\"\" for decoration)")
        if re.fullmatch(r"h[1-6]", tag):
            sec = next((x[1].get("id", "?") for x in reversed(self.stack[:-1]) if x[0] in ("section", "main", "article", "dialog") and x[1].get("id")), "page")
            self.headings.append((line, int(tag[1]), sec))
        if tag in ("button", "a"):
            self.open_named.append([tag, a, "", line])
        if tag == "a" and "href" not in a and a.get("role") != "button":
            self.add(line, "a without href is not focusable; use a button or add href")
        if tag in ("div", "span", "li", "p", "td") and ("onclick" in a) and a.get("role") not in ("button", "link"):
            self.add(line, f"{tag} with onclick is not a button; use <button>")
        if a.get("tabindex", "").lstrip("+").isdigit() and int(a["tabindex"]) > 0:
            self.add(line, "positive tabindex changes focus order; remove it")
        for k in ("src", "href"):
            v = a.get(k, "")
            if tag in ("script", "link", "img", "iframe", "source") and re.match(r"(https?:)?//", v):
                self.add(line, f"{tag} loads from the network ({v[:60]}); prototypes must run offline")
        if a.get("aria-label") and self.open_named and self.open_named[-1][1] is a:
            self.open_named[-1][2] += a["aria-label"]
        if tag == "img" and a.get("alt") and self.open_named:
            self.open_named[-1][2] += a["alt"]
        if tag == "svg" and self.open_named and (a.get("aria-label") or a.get("role") == "img"):
            self.open_named[-1][2] += a.get("aria-label", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "style":
            self.in_style = False
        if tag == "label":
            self.label_depth = max(0, self.label_depth - 1)
        if tag in ("button", "a") and self.open_named and self.open_named[-1][0] == tag:
            t, a, text, line = self.open_named.pop()
            if not (text.strip() or a.get("aria-labelledby") or a.get("title")):
                self.add(line, f"{t} has no text or aria-label")
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.in_style:
            self.css.append(data)
            return
        if self.in_title:
            self.title += data
        for o in self.open_named:
            o[2] += data
        if not any(t in ("script", "style") for t, _ in self.stack):
            self.text.append(data)


def lint_file(path):
    d = Doc()
    src = open(path, encoding="utf-8", errors="replace").read()
    d.feed(src)
    f = d.findings
    css = "\n".join(d.css)
    for href in re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)', src):
        p = os.path.join(os.path.dirname(path), href)
        if os.path.exists(p):
            css += "\n" + open(p, encoding="utf-8", errors="replace").read()
    if not d.lang:
        f.append((1, "html has no lang attribute (use lang=\"en-GB\")"))
    if not d.title.strip():
        f.append((1, "no <title>"))
    if d.viewport is None:
        f.append((1, "no viewport meta tag"))
    elif re.search(r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b", d.viewport):
        f.append((1, "viewport disables zoom; remove user-scalable/maximum-scale"))
    for line, tag, a, wrapped in d.controls:
        if not (wrapped or a.get("aria-label") or a.get("aria-labelledby") or a.get("id") in d.labels_for):
            f.append((line, f"{tag} {a.get('id') or a.get('name') or ''} has no label"))
        if a.get("placeholder") and not (wrapped or a.get("id") in d.labels_for):
            f.append((line, "placeholder used instead of a visible label"))
    by_sec = {}
    for line, lvl, sec in d.headings:
        by_sec.setdefault(sec, []).append((line, lvl))
    for sec, hs in by_sec.items():
        n1 = sum(1 for _, l in hs if l == 1)
        if sec != "page" and n1 != 1:
            f.append((hs[0][0], f"screen '{sec}' has {n1} h1 headings; it needs exactly one"))
        prev = 0
        for line, lvl in hs:
            if prev and lvl > prev + 1:
                f.append((line, f"heading level jumps from h{prev} to h{lvl} in '{sec}'"))
            prev = lvl
    if not d.headings:
        f.append((1, "no headings"))
    if re.search(r"outline\s*:\s*(none|0)\b", css) and ":focus-visible" not in css and not re.search(r":focus[^{]*\{[^}]*(outline|box-shadow)\s*:\s*(?!none|0)", css):
        f.append((1, "CSS removes outlines and defines no visible focus style"))
    if ":focus" not in css:
        f.append((1, "CSS defines no focus style; add :focus-visible with a clear outline"))
    for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", css):
        if float(m.group(1)) < 12:
            f.append((1, f"font-size {m.group(1)}px is too small"))
    for m in re.finditer(r"font-size\s*:\s*(0?\.\d+)rem", css):
        if float(m.group(1)) * 16 < 12:
            f.append((1, f"font-size {m.group(1)}rem is under 12px"))
    if re.search(r"@import\s+url\(['\"]?https?:|url\(['\"]?https?:", css):
        f.append((1, "CSS loads a resource from the network"))
    if re.search(r"lorem ipsum|placeholder text|todo:", " ".join(d.text), re.I):
        f.append((1, "placeholder text found (lorem ipsum / TODO)"))
    tokens = dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b", css))
    pairs = [("--text", "--bg"), ("--text", "--surface"), ("--text-muted", "--bg"), ("--text-muted", "--surface"),
             ("--on-primary", "--primary"), ("--primary", "--bg"), ("--primary", "--surface")]
    for fg, bg in pairs:
        if fg in tokens and bg in tokens:
            try:
                r = ratio(tokens[fg], tokens[bg])
            except ValueError:
                continue
            if r < 4.5:
                f.append((1, f"contrast {fg} {tokens[fg]} on {bg} {tokens[bg]} is {r:.2f}:1 (needs 4.5:1 for text)"))
    for fg, bg in (("--border", "--bg"), ("--border", "--surface"), ("--focus", "--bg"), ("--focus", "--surface")):
        if fg in tokens and bg in tokens:
            try:
                r = ratio(tokens[fg], tokens[bg])
            except ValueError:
                continue
            if r < 3:
                f.append((1, f"contrast {fg} {tokens[fg]} on {bg} {tokens[bg]} is {r:.2f}:1 (control edges and focus rings need 3:1; fine if this token is only decorative)"))
    return sorted(set(f))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    target = sys.argv[1]
    files = [target] if target.endswith(".html") else sorted(
        os.path.join(r, n) for r, _, ns in os.walk(target) for n in ns if n.endswith(".html"))
    if not files:
        sys.exit(f"no .html files in {target}")
    total = 0
    for p in files:
        for line, msg in lint_file(p):
            total += 1
            print(f"{p}:{line}: {msg}")
    print(f"{total} finding(s) in {len(files)} file(s)")
    sys.exit(1 if total else 0)
