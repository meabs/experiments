"""Opens every run's storyboard in a headless browser and measures it. No model is involved.

For each run (results/<stage>/<arm>/runs/<brief>/<arm>/codex/<rep>/artefacts/storyboard/):
  - reads screens.json (the delivery contract) and opens index.html#<id> for each screen, phone size 390x844;
  - saves a full-page screenshot (eval/.../screens/NN-<id>.png) and the screen's visible text;
  - runs axe-core 4.10.3 with the WCAG 2.0, 2.1 and 2.2 level A and AA rule tags;
  - measures: sideways overflow at 320 px wide; the size of every visible interactive element (24 px and 44 px
    thresholds); clickable things that can't be reached by keyboard; console errors; network requests.
Writes results/<stage>/eval/<brief>/<arm>/<rep>/eval.json. Runs with no storyboard or a broken contract are recorded
as such, not skipped.

Usage: ~/code/benchmark/webmcp-exp/env-plain/bin/python shoot.py <stage dir> [brief/arm/rep ...]
"""
import hashlib, json, os, re, sys
from pathlib import Path

from playwright.sync_api import sync_playwright

AXE = Path.home() / "code/benchmark/df-work/axe/package/axe.min.js"
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
MAX_SCREENS = 40
MEASURE = r"""() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.01; };
  const focusable = el => el.matches('a[href],button,input,select,textarea,summary,[tabindex]:not([tabindex="-1"])') && !el.disabled;
  const inter = [...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[role=tab],[role=switch],[role=checkbox],[role=radio]')].filter(vis);
  const sizes = inter.map(el => { const r = el.getBoundingClientRect(); let w = r.width, h = r.height;
    if (el.matches('input[type=checkbox],input[type=radio]')) { const l = el.closest('label') || (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)); if (l) { const lr = l.getBoundingClientRect(); w = Math.max(w, lr.width); h = Math.max(h, lr.height); } }
    const inline = el.matches('a') && getComputedStyle(el).display.startsWith('inline') && el.parentElement && el.parentElement.innerText.trim().length > el.innerText.trim().length + 15;
    return {tag: el.tagName.toLowerCase(), w: Math.round(w), h: Math.round(h), inline, text: (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 40)}; });
  const unreachable = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!vis(el)) continue;
    const own = getComputedStyle(el).cursor === 'pointer';
    const par = el.parentElement && getComputedStyle(el.parentElement).cursor === 'pointer';
    if (!(el.hasAttribute('onclick') || (own && !par))) continue;
    if (focusable(el) || el.closest('a[href],button,label,summary,[tabindex]:not([tabindex="-1"])')) continue;
    if (el.matches('label') || el.querySelector('a[href],button,input,select,textarea')) continue;
    unreachable.push((el.tagName.toLowerCase() + ' ' + (el.innerText || '').trim().slice(0, 40)).trim());
  }
  const h1 = [...document.querySelectorAll('h1')].filter(vis).length;
  return {sizes, unreachable, h1, title: document.title, lang: document.documentElement.lang || '',
          text: document.body.innerText, height: document.documentElement.scrollHeight};
}"""


def screens_of(proto):
    f = proto / "screens.json"
    if not f.exists():
        return None, "no screens.json"
    try:
        j = json.loads(f.read_text(errors="replace"))
    except ValueError as e:
        return None, f"screens.json is not JSON: {e}"
    if isinstance(j, dict):
        j = j.get("screens", j.get("items", []))
    out = []
    for s in j if isinstance(j, list) else []:
        if isinstance(s, str):
            out.append({"id": s, "title": s})
        elif isinstance(s, dict) and s.get("id"):
            out.append({"id": str(s["id"]).lstrip("#"), "title": str(s.get("title", s["id"]))})
    return (out, None) if out else (None, "screens.json lists no screens")


def one(browser, run_dir, out_dir):
    proto = run_dir / "artefacts" / "storyboard"
    res = {"run": str(run_dir), "storyboard": (proto / "index.html").exists(), "contract_error": None, "screens": []}
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in (out_dir / "screens").glob("*.png") if (out_dir / "screens").exists() else []:
        old.unlink()
    (out_dir / "screens").mkdir(exist_ok=True)
    if not res["storyboard"]:
        res["contract_error"] = "no storyboard/index.html"
        (out_dir / "eval.json").write_text(json.dumps(res, indent=1))
        return res
    screens, err = screens_of(proto)
    res["contract_error"] = err
    if screens is None:
        screens = [{"id": "", "title": "index.html (no screen list)"}]
    res["listed"] = len(screens)
    url = (proto / "index.html").resolve().as_uri()
    for n, s in enumerate(screens[:MAX_SCREENS], 1):
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, has_touch=True,
                                  is_mobile=True, locale="en-GB", reduced_motion="reduce")
        page = ctx.new_page()
        errors, requests = [], []
        page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.on("request", lambda r: requests.append(r.url[:120]) if not r.url.startswith(("file:", "data:", "blob:", "about:")) else None)
        rec = {"n": n, "id": s["id"], "title": s["title"]}
        own_errors = None
        try:
            page.goto(url + ("#" + s["id"] if s["id"] else ""), wait_until="load", timeout=20000)
            page.wait_for_timeout(900)
            page.evaluate("() => { if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur(); }")  # a focus ring left by script-moved focus is a capture artefact, not part of the design
            m = page.evaluate(MEASURE)
            name = f"{n:02d}-{re.sub(r'[^a-zA-Z0-9_-]+', '_', s['id'])[:40] or 'index'}.png"
            page.screenshot(path=str(out_dir / "screens" / name), full_page=True, clip=None) if m["height"] <= 3600 else \
                page.screenshot(path=str(out_dir / "screens" / name), clip={"x": 0, "y": 0, "width": 390, "height": 3600})
            rec.update(img_hash=hashlib.sha1((out_dir / "screens" / name).read_bytes()).hexdigest()[:12], png=name, text=m["text"], text_hash=hashlib.sha1(re.sub(r"\s+", " ", m["text"]).encode()).hexdigest()[:12],
                       h1=m["h1"], title_tag=m["title"], lang=m["lang"], height=m["height"], sizes=m["sizes"],
                       unreachable=m["unreachable"])
            own_errors = list(errors)  # axe's own stylesheet fetches fail on file:// pages; they are not the storyboard's errors
            page.add_script_tag(path=str(AXE))
            ax = page.evaluate("async tags => { const r = await axe.run(document, {runOnly: {type: 'tag', values: tags}, resultTypes: ['violations']}); return r.violations.map(v => ({id: v.id, impact: v.impact, nodes: v.nodes.length, help: v.help})); }", TAGS)
            rec["axe"] = ax
            page.set_viewport_size({"width": 320, "height": 844})
            page.wait_for_timeout(250)
            rec["overflow_320"] = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
        except Exception as e:  # a screen that fails to load is a result, not a crash
            rec["error"] = str(e)[:300]
        rec["console_errors"], rec["network"] = (errors if own_errors is None else own_errors)[:10], requests[:10]
        res["screens"].append(rec)
        ctx.close()
    hashes = [r.get("img_hash") for r in res["screens"] if r.get("img_hash")]  # distinct by what is shown, not by page text (a one-page storyboard has the same text at every address)
    res["distinct_screens"] = len(set(hashes))
    (out_dir / "eval.json").write_text(json.dumps(res, indent=1))
    return res


def main(stage, only):
    stage = Path(stage)
    runs = sorted(p for p in stage.glob("*/runs/*/*/codex/*") if p.is_dir())
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for r in runs:
            brief, arm, rep = r.parts[-4], r.parts[-3], r.parts[-1]
            key = f"{brief}/{arm}/{rep}"
            if only and key not in only:
                continue
            res = one(browser, r, stage / "eval" / brief / arm / rep)
            ax = sum(len(s.get("axe", [])) for s in res["screens"])
            print(key, "screens", len(res["screens"]), "distinct", res.get("distinct_screens"), "axe rule hits", ax,
                  "contract", res["contract_error"] or "ok", flush=True)
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1], set(sys.argv[2:]))
