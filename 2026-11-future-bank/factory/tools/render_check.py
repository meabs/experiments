#!/usr/bin/env python3
"""Rendered checks with headless Chrome. Usage: python3 tools/render_check.py <folder> [frame-id ...]

Opens <folder>/index.html at each frame address (ids from <folder>/screens.json, or the ids given) in a temporary copy
with a small measuring script added, and reports what is actually rendered:
  - text whose colour against its nearest solid background is under 4.5:1 (3:1 for large text);
  - controls (links, buttons, inputs) smaller than 24 px (fails) or 44 px (aim) in either direction;
  - controls with no accessible name; fields with no label;
  - number of visible h1 elements.
Limits: headless Chrome cannot go narrower than 500 px, so this does NOT check reflow at 320 px; text over images or
gradients is skipped; it does not test keyboard order or screen readers. Needs google-chrome on the path. The result is
evidence for the accessibility table, not proof of conformance. Exit code 1 if any frame has a finding.
"""
import json, os, re, subprocess, sys
from html import unescape

JS = r"""<script>window.addEventListener('load', function () { setTimeout(function () {
  var vis = function (e) { var r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.01; };
  var rgb = function (c) { var m = c.match(/[\d.]+/g); return m ? m.map(Number) : [0, 0, 0, 1]; };
  var chan = function (v) { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  var lum = function (c) { return 0.2126 * chan(c[0]) + 0.7152 * chan(c[1]) + 0.0722 * chan(c[2]); };
  var bg = function (e) { var x = e; while (x) { var s = getComputedStyle(x); if (s.backgroundImage !== 'none') return null; var c = rgb(s.backgroundColor); if (c.length < 4) c.push(1); if (c[3] >= 0.99) return c; x = x.parentElement; } return [255, 255, 255, 1]; };
  var labelFor = function (el) { return el.closest('label') || (el.id && document.querySelector('label[for="' + el.id + '"]')); };
  var out = { low: [], small: [], noname: [], h1: 0 };
  out.h1 = Array.prototype.filter.call(document.querySelectorAll('h1'), vis).length;
  var seen = {};
  Array.prototype.forEach.call(document.querySelectorAll('body *'), function (el) {
    if (!vis(el)) return;
    var t = Array.prototype.filter.call(el.childNodes, function (n) { return n.nodeType === 3; }).map(function (n) { return n.textContent.trim(); }).join(' ').trim();
    if (t) {
      var s = getComputedStyle(el), b = bg(el);
      if (b) {
        var f = rgb(s.color), a = f.length > 3 ? f[3] : 1;
        var fg = [0, 1, 2].map(function (i) { return f[i] * a + b[i] * (1 - a); });
        var l1 = lum(fg), l2 = lum(b), r = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
        var px = parseFloat(s.fontSize), bold = +s.fontWeight >= 700, large = px >= 24 || (px >= 18.66 && bold);
        var key = t.slice(0, 30) + r.toFixed(1);
        if (r < (large ? 3 : 4.5) && !seen[key]) { seen[key] = 1; out.low.push(t.slice(0, 40) + ' ' + r.toFixed(2) + ':1'); }
      }
    }
    if (el.matches('a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link]')) {
      var q = el.getBoundingClientRect(), inl = el.matches('a') && getComputedStyle(el).display.indexOf('inline') === 0, w = q.width, h = q.height;
      if (el.matches('input[type=checkbox],input[type=radio]')) { var l = labelFor(el); if (l) { var lr = l.getBoundingClientRect(); w = Math.max(w, lr.width); h = Math.max(h, lr.height); } }
      if (!inl && Math.min(w, h) < 44) out.small.push((el.innerText || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 30) + ' ' + Math.round(w) + 'x' + Math.round(h));
      var isField = el.matches('input,select,textarea');
      var named = isField ? (labelFor(el) || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) : ((el.innerText || '').trim() || el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('aria-labelledby'));
      if (!named) out.noname.push(el.tagName.toLowerCase() + ' ' + (el.id || el.name || ''));
    }
  });
  var pre = document.createElement('pre'); pre.id = '__rc'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
}, 600); });</script>"""


def run(folder, fid):
    src = open(os.path.join(folder, "index.html"), encoding="utf-8", errors="replace").read()
    tmp = os.path.join(folder, "__render_check.html")
    open(tmp, "w", encoding="utf-8").write(re.sub(r"</body>", lambda m: JS + m.group(0), src, count=1, flags=re.I) if re.search(r"</body>", src, re.I) else src + JS)
    try:
        p = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--window-size=500,900",
                            "--virtual-time-budget=4000", "--dump-dom", "file://" + os.path.abspath(tmp) + ("#" + fid if fid else "")],
                           capture_output=True, text=True, timeout=90)
    finally:
        os.remove(tmp)
    m = re.search(r'<pre id="__rc">(.*?)</pre>', p.stdout, re.S)
    return json.loads(unescape(m.group(1))) if m else None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    folder, ids = sys.argv[1], sys.argv[2:]
    if not ids:
        try:
            ids = [s["id"] if isinstance(s, dict) else s for s in json.load(open(os.path.join(folder, "screens.json")))]
        except (OSError, ValueError):
            ids = [""]
    bad = 0
    for fid in ids:
        r = run(folder, fid)
        if r is None:
            print(f"{fid or 'index'}: could not measure (is google-chrome installed?)")
            bad += 1
            continue
        issues = [f"low contrast: {x}" for x in r["low"][:4]] + [f"under 44 px: {x}" for x in r["small"][:4]] + \
                 [f"no name or label: {x}" for x in r["noname"][:3]] + ([f"{r['h1']} visible h1" ] if r["h1"] != 1 else [])
        bad += bool(issues)
        print(f"{fid or 'index'}: " + ("ok" if not issues else "; ".join(issues)))
    sys.exit(1 if bad else 0)
