#!/usr/bin/env python3
"""Renders every frame of a storyboard or prototype to a PNG so it can be looked at. Usage: python3 tools/screenshot.py <folder>
Opens <folder>/index.html at each frame address (ids from <folder>/screens.json) in headless Chrome at 1280 px wide and saves
<folder>/../design/shots/<id>.png (created if missing). Prints the paths. Needs google-chrome on the path."""
import json, os, subprocess, sys
folder = os.path.abspath(sys.argv[1])
ids = [s["id"] for s in json.load(open(os.path.join(folder, "screens.json")))]
out = os.path.join(os.path.dirname(folder), "design", "shots")
os.makedirs(out, exist_ok=True)
for i in ids:
    dest = os.path.join(out, f"{i}.png")
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--window-size=1280,1000",
                    f"--screenshot={dest}", f"file://{folder}/index.html#{i}"], capture_output=True, timeout=60)
    print(dest if os.path.exists(dest) else f"failed: {i}")
