"""Tables for the article, from <out>/runs.jsonl. Prints Markdown.

Rates are runs of runs with Wilson 95% intervals. "Architecture" rows are the four architectures, each AI one with
both models. Per level, per wording (original / paraphrased) and per account size (small / large).
Consistency: the share of case x wording x account conditions where every repetition got the same outcome.
Usage: python3 -I analyse.py <out>   (reads <out>/runs.jsonl, or runs.jsonl.gz as exported to results/main)
"""
import collections, gzip, json, math, os, statistics as st, sys

ARMS = [("rules", "none", "Plain code"), ("single", "openai/gpt-6-luna", "One call, Luna"),
        ("single", "qwen/qwen3.7-flash", "One call, Qwen"), ("workflow", "openai/gpt-6-luna", "Workflow, Luna"),
        ("workflow", "qwen/qwen3.7-flash", "Workflow, Qwen"), ("agent", "openai/gpt-6-luna", "Agent, Luna"),
        ("agent", "qwen/qwen3.7-flash", "Agent, Qwen")]
LEVELS = {1: "1 simple", 2: "2 multi-step", 3: "3 branching", 4: "4 recovery", 5: "5 unanticipated"}


def wilson(k, n, z=1.96):
    if not n:
        return 0, 0
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0, c - h), min(1, c + h)


def pct(rs, outcome="resolved", ci=False):
    k, n = sum(r["outcome"] == outcome for r in rs), len(rs)
    if not n:
        return "–"
    s = f"{100 * k / n:.0f}%"
    if ci:
        lo, hi = wilson(k, n)
        s += f" ({100 * lo:.0f}–{100 * hi:.0f})"
    return s


def main(out):
    path = os.path.join(out, "runs.jsonl")
    runs = [json.loads(line) for line in (open(path) if os.path.exists(path) else gzip.open(path + ".gz", "rt"))]
    by = collections.defaultdict(list)
    for r in runs:
        by[(r["arm"], r["model"])].append(r)
    print(f"# Do you actually need an agent? Analysis\n\n{len(runs)} runs from `{os.path.basename(os.path.abspath(out))}`. "
          f"Crashed: {sum(r['outcome'] == 'crashed' for r in runs)}. Transport retries (OpenRouter): "
          f"{sum(r.get('transport_retries', 0) for r in runs)}.\n")

    print("## Resolved, by level\n\nShare of runs resolved (right actions and a reply with the required facts); "
          "**higher is better**. Both wordings and both account sizes pooled.\n")
    print("| Architecture | " + " | ".join(LEVELS.values()) + " | All |\n|" + " --- |" * 7)
    for arm, model, name in ARMS:
        rs = by[(arm, model)]
        print(f"| {name} | " + " | ".join(pct([r for r in rs if r["level"] == lv]) for lv in LEVELS)
              + f" | **{pct(rs, ci=True)}** |")

    for title, key, vals in (("wording", "wording", ["original", "paraphrased"]), ("account size", "history", ["small", "large"])):
        print(f"\n## Resolved, by {title}\n\nShare resolved; **higher is better**.\n")
        print("| Architecture | " + " | ".join(vals) + " |\n|" + " --- |" * (len(vals) + 1))
        for arm, model, name in ARMS:
            rs = by[(arm, model)]
            print(f"| {name} | " + " | ".join(pct([r for r in rs if r.get(key, "small") == v], ci=True) for v in vals) + " |")

    print("\n## How runs ended\n\nShare of all runs. Resolved: **higher is better**. Escalated: handed to a human when "
          "the policy didn't require it (safe, but a person has to do it). Wrong: missed action or missing information. "
          "Harmful: a refund, replacement, cancellation or address change the policy didn't call for. "
          "**Lower is better** for the last three.\n")
    print("| Architecture | Resolved | Escalated | Wrong | Harmful | Harmful runs (count) |\n| --- | --- | --- | --- | --- | --- |")
    for arm, model, name in ARMS:
        rs = by[(arm, model)]
        print(f"| {name} | {pct(rs)} | {pct(rs, 'escalated')} | {pct(rs, 'wrong')} | {pct(rs, 'harmful')} | "
              f"{sum(r['outcome'] == 'harmful' for r in rs)} |")

    print("\n## Cost, speed and consistency\n\nCost at OpenRouter's billed price. **Lower is better** for cost, calls and "
          "time; **higher is better** for consistency (conditions where every repetition ended the same way).\n")
    print("| Architecture | Accounts | Cost per 1,000 emails, $ | Cost per resolved email, $ | Median model calls | "
          "Median prompt tokens | Median seconds | Consistency |\n| --- | --- | --- | --- | --- | --- | --- | --- |")
    for arm, model, name in ARMS:
        for h in ("small", "large"):
            rs = [r for r in by[(arm, model)] if r.get("history", "small") == h]
            if not rs:
                continue
            cost = sum(r["cost"] for r in rs)
            res = sum(r["outcome"] == "resolved" for r in rs)
            groups = collections.defaultdict(set)
            for r in rs:
                groups[(r["case"], r["wording"])].add(r["outcome"])
            cons = sum(len(v) == 1 for v in groups.values()) / len(groups)
            print(f"| {name} | {h} | {1000 * cost / len(rs):.2f} | {cost / res if res else float('nan'):.5f} | "
                  f"{st.median(r.get('llm_calls', 0) for r in rs):.0f} | {st.median(r.get('prompt_tokens', 0) for r in rs):,.0f} | "
                  f"{st.median(r['seconds'] for r in rs):.1f} | {100 * cons:.0f}% |")

    print("\n## Per case (resolved runs of all runs)\n")
    cases = sorted({r["case"] for r in runs})
    print("| Case | " + " | ".join(n for _, _, n in ARMS) + " |\n|" + " --- |" * (len(ARMS) + 1))
    for c in cases:
        cells = []
        for arm, model, _ in ARMS:
            rs = [r for r in by[(arm, model)] if r["case"] == c]
            k = sum(r["outcome"] == "resolved" for r in rs)
            h = sum(r["outcome"] == "harmful" for r in rs)
            cells.append(f"{k}/{len(rs)}" + (f" ({h} harmful)" if h else ""))
        print(f"| {c} | " + " | ".join(cells) + " |")
    print(f"\nTotal cost: ${sum(r['cost'] for r in runs):.2f}.")


if __name__ == "__main__":
    main(sys.argv[1])
