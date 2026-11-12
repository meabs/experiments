#!/usr/bin/env python3
"""Contrast ratio of two colours (WCAG 2.x). Usage: python3 tools/contrast.py "#1a1a2e" "#ffffff" [more pairs ...]

Accepts #rgb, #rrggbb and rgb(r, g, b). Prints the ratio and whether it passes AA for normal text (4.5), for large
text and for control edges, icons and focus rings (3.0). Exit code 1 if any pair is under 4.5.
"""
import re
import sys


def parse(c):
    c = c.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3})", c)
    if m:
        return tuple(int(ch * 2, 16) for ch in m.group(1))
    m = re.fullmatch(r"#([0-9a-f]{6})", c)
    if m:
        return tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
    m = re.fullmatch(r"rgb\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)\s*\)", c)
    if m:
        return tuple(int(x) for x in m.groups())
    raise ValueError(f"can't read colour {c!r}")


def luminance(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = luminance(parse(a)), luminance(parse(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2:
        sys.exit(__doc__)
    bad = False
    for fg, bg in zip(args[::2], args[1::2]):
        r = ratio(fg, bg)
        verdict = "passes AA text" if r >= 4.5 else ("large text and control edges only" if r >= 3 else "FAILS")
        bad |= r < 4.5
        print(f"{fg} on {bg}: {r:.2f}:1  {verdict}")
    sys.exit(1 if bad else 0)
