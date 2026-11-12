"""Exploratory re-capture for the 'looks' confound (see README amendment 1): crops every screen to its interior.
For each screen of each run, opens index.html#<id> in a 1280 px wide desktop viewport (so a phone frame is shown at
its natural size, not squeezed into a 390 px viewport), finds the frame element with that id, then the screen inside it:
the smallest element 280-520 px wide and at least 420 px high that still contains every control and icon in the frame
(this steps in from a card or bezel to the glass, and leaves captions behind). The element is saved as a PNG: no captions, bezel,
tags or page background. Fallback when nothing fits: the 390 px full-page capture is used and flagged.
Output: <stage>/eval-crop/<brief>/<arm>/<rep>/crops/NN.png and crop.json. Nothing here changes the primary data.
Usage: ~/code/benchmark/webmcp-exp/env-plain/bin/python crop.py <stage dir> [brief/arm/rep ...]
"""
import json, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

FIND = r"""(id) => {
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  let root = id ? document.getElementById(id) : null;
  if (!root && id) root = document.querySelector('[data-frame="' + id + '"],[data-screen="' + id + '"],[data-id="' + id + '"]');
  if (!root || !vis(root)) root = document.body;
  const area = e => { const r = e.getBoundingClientRect(); return r.width * r.height; };
  const ok = e => { const r = e.getBoundingClientRect(); return vis(e) && r.width >= 280 && r.width <= 520 && r.height >= 420; };
  const ui = e => e.querySelectorAll('button,a[href],input,select,textarea,svg,img,[role=button]').length;
  const all = [root, ...root.querySelectorAll('*')].filter(ok);
  if (!all.length) return false;
  const top = Math.max(...all.map(ui));
  if (top === 0) return all.reduce((a, b) => (area(b) > area(a) ? b : a));
  const cur = all.filter(e => ui(e) === top).reduce((a, b) => (area(b) < area(a) ? b : a));
  return cur;
}"""


def main(stage, only):
    stage = Path(stage)
    with sync_playwright() as p:
        br = p.chromium.launch()
        for ev in sorted(stage.glob("eval/*/*/*/eval.json")):
            brief, arm, rep = ev.parts[-4], ev.parts[-3], ev.parts[-2]
            key = f"{brief}/{arm}/{rep}"
            if only and key not in only:
                continue
            e = json.loads(ev.read_text())
            run = stage / arm / "runs" / brief / arm / "codex" / rep / "artefacts" / "storyboard" / "index.html"
            out = stage / "eval-crop" / brief / arm / rep
            shutil.rmtree(out, ignore_errors=True)
            (out / "crops").mkdir(parents=True)
            recs = []
            for s in e["screens"]:
                if not s.get("png"):
                    continue
                name = s["png"]
                rec = {"n": s["n"], "id": s["id"], "png": name, "method": "fallback"}
                try:
                    ctx = br.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=2, locale="en-GB", reduced_motion="reduce")
                    page = ctx.new_page()
                    page.goto(run.resolve().as_uri() + ("#" + s["id"] if s["id"] else ""), wait_until="load", timeout=20000)
                    page.wait_for_timeout(700)
                    page.evaluate("() => { if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur(); }")
                    h = page.evaluate_handle(FIND, s["id"])
                    el = h.as_element()
                    if el:
                        info = el.evaluate("e => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return {l: parseFloat(s.borderLeftWidth), t: parseFloat(s.borderTopWidth), r: parseFloat(s.borderRightWidth), b: parseFloat(s.borderBottomWidth), x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height}; }")
                        clip = {"x": info["x"] + info["l"], "y": info["y"] + info["t"], "width": info["w"] - info["l"] - info["r"], "height": info["h"] - info["t"] - info["b"]}  # inside the border: a phone bezel is a border
                        page.screenshot(path=str(out / "crops" / name), full_page=True, clip=clip)
                        rec.update(method="crop", w=round(clip["width"]), h=round(clip["height"]))
                    ctx.close()
                except Exception as ex:
                    rec["error"] = str(ex)[:200]
                if rec["method"] == "fallback":
                    shutil.copy(ev.parent / "screens" / name, out / "crops" / name)
                recs.append(rec)
            (out / "crop.json").write_text(json.dumps(recs, indent=1))
            print(key, sum(r["method"] == "crop" for r in recs), "cropped of", len(recs), flush=True)
        br.close()


if __name__ == "__main__":
    main(sys.argv[1], set(sys.argv[2:]))
