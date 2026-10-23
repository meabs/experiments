"""Build a Codex model catalog entry for the local model by cloning gpt-5.6-luna's entry (Codex 0.157.0).
Usage: python3 -I make_catalog.py <upstream models.json> <out.json> [field=json ...]"""
import json, sys
src, out, *over = sys.argv[1:]
luna = next(m for m in json.load(open(src))["models"] if m["slug"] == "gpt-5.6-luna")
m = dict(luna, slug="qwen3.8:27b", display_name="qwen3.8:27b (local, luna profile)",
         context_window=65536, max_context_window=65536, auto_compact_token_limit=56000,
         prefer_websockets=False, input_modalities=["text"], service_tiers=[], additional_speed_tiers=[])
for kv in over:
    k, v = kv.split("=", 1)
    if k not in luna: sys.exit(f"unknown catalog field: {k}")
    m[k] = json.loads(v)
json.dump({"models": [m]}, open(out, "w"), indent=1)
print({k: m[k] for k in ("apply_patch_tool_type", "tool_mode", "use_responses_lite", "shell_type", "prefer_websockets")})
