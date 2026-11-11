"""Judging pages: tiles a run's screenshots (from shoot.py) three to a page, in screens.json order.
Each tile is the screen at 390 px wide (its top 1100 px), numbered, with no titles or ids (they could reveal the arm).
Pages p1.png ... p6.png (up to 18 screens). The looks-only judgement uses p1 and p2 (the first six screens, the same
amount of material from both arms); the whole-design judgement uses every page.
Usage: python3 sheet.py <stage dir>
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

TW, TH, PAD, PER, MAXP = 390, 1100, 24, 3, 6
BG = "#d9d9de"


def font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def page(pngs, first, out):
    im = Image.new("RGB", (PAD + PER * (TW + PAD), PAD + TH + 40 + PAD), BG)
    d = ImageDraw.Draw(im)
    for i, p in enumerate(pngs):
        s = Image.open(p).convert("RGB")
        s = s.resize((TW, round(s.height * TW / s.width)), Image.LANCZOS)
        s = s.crop((0, 0, TW, min(TH, s.height)))
        x = PAD + i * (TW + PAD)
        d.text((x, PAD), str(first + i), fill="#333", font=font(26))
        im.paste(s, (x, PAD + 40))
    im.save(out, optimize=True)


if __name__ == "__main__":
    stage = Path(sys.argv[1])
    for ev in sorted(stage.glob("eval/*/*/*/eval.json")):
        e = json.loads(ev.read_text())
        pngs = [ev.parent / "screens" / s["png"] for s in e["screens"] if s.get("png")]
        for old in ev.parent.glob("p[0-9].png"):
            old.unlink()
        for n in range(min(MAXP, -(-len(pngs) // PER))):
            page(pngs[n * PER:(n + 1) * PER], n * PER + 1, ev.parent / f"p{n + 1}.png")
        print(ev.parent.relative_to(stage), len(pngs), "screens")
