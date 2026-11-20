import sys, os, json
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, "..")
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "results", "demo", "demo-games.json")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "diagrams", "observer-demo.html")
t = open(os.path.join(root, "diagrams", "observer.template.html")).read()
open(out, "w").write(t.replace("/*DATA*/null", json.dumps(json.load(open(src)), separators=(",", ":"))))
print(out, os.path.getsize(out) // 1024, "KB")
