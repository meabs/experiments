"""Checks made after the runs (not part of the fixed analysis): model and effort in every Codex session file, the token
breakdown, total wall time and energy per arm, and what the same tokens would cost at gpt-5.6-luna list prices.
Reads the run folder (the session files are under agent-homes/, which are not published), so run it before export.

Usage: python3 -I extra_checks.py <out dir> > results/extra-checks.md
"""
import collections, glob, json, os, sys
from datetime import datetime

ARMS = ["no_okf", "okf", "source"]
PRICE_KWH = 0.25
# gpt-5.6-luna list prices per million tokens, as in the other experiments (split-spec/scripts/audit_run.py)
P_IN, P_CACHED, P_OUT = 0.20, 0.02, 1.20


def session_stats(path):
    model = effort = usage = None
    for line in open(path, errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        p = e.get("payload", {})
        if e.get("type") == "turn_context":
            model, effort = p.get("model"), p.get("effort")
        if p.get("type") == "token_count" and p.get("info"):
            usage = p["info"].get("total_token_usage")
    return model, effort, usage or {}


def main(out):
    power = []
    for line in open(os.path.join(out, "power.csv")).read().splitlines()[1:]:
        try:
            t, w = line.split(",")
            power.append((float(t), float(w)))
        except ValueError:
            pass
    seen = collections.Counter()
    print("# okf-local: checks after the runs\n")
    print("Made after the runs, from each run's Codex session file and the power log; not part of the fixed analysis.\n")
    rows = []
    for arm in ARMS:
        tok = collections.Counter()
        secs = wh = 0.0
        n = 0
        for rj in glob.glob(os.path.join(out, arm, "runs", "*", arm, "codex", "*", "run.json")):
            r = json.load(open(rj))
            n += 1
            secs += r["seconds"]
            start = datetime.fromisoformat(r["started"]).timestamp()
            wh += sum(w for t, w in power if start <= t <= start + r["seconds"]) / 3600
            home = os.path.join(out, arm, "agent-homes", f"{r['question']}_{arm}_codex_{r['rep']}", ".codex", "sessions")
            files = glob.glob(os.path.join(home, "**", "*.jsonl"), recursive=True)
            for f in files:
                model, effort, usage = session_stats(f)
                seen[(arm, model, effort)] += 1
                tok.update({k: usage.get(k, 0) for k in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")})
        usd = ((tok["input_tokens"] - tok["cached_input_tokens"]) * P_IN + tok["cached_input_tokens"] * P_CACHED + tok["output_tokens"] * P_OUT) / 1e6
        rows.append((arm, n, tok, secs, wh, usd))

    print("## Model and effort in the session files\n")
    for (arm, model, effort), k in sorted(seen.items()):
        print(f"- `{arm}`: {k} session files name `{model}` at `{effort}` effort.")
    print()
    print("## Tokens, time, energy and the hosted-price equivalent, per run (mean over the arm's 20 runs)\n")
    print("Lower is better in every column. Cached input is input the model server had already processed in an earlier turn of the "
          "same run. Hosted-price equivalent: what the same tokens would cost at gpt-5.6-luna list prices "
          f"(${P_IN} per million uncached input, ${P_CACHED} cached, ${P_OUT} output); the local runs cost only electricity.\n")
    print("| Arm | Input tokens | of which cached | Output tokens | Wall time, total for 20 runs | Energy per run, Wh | Electricity per run (£0.25/kWh) | Hosted-price equivalent per run |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for arm, n, tok, secs, wh, usd in rows:
        print(f"| `{arm}` | {tok['input_tokens'] / n / 1000:.0f}k | {tok['cached_input_tokens'] / n / 1000:.0f}k | "
              f"{tok['output_tokens'] / n / 1000:.1f}k | {secs / 3600:.1f} h | {wh / n:.1f} | £{wh / n / 1000 * PRICE_KWH:.4f} | ${usd / n:.3f} |")
    print("\nReasoning tokens: Ollama reports none separately, so they are counted in output.")


if __name__ == "__main__":
    main(sys.argv[1])
