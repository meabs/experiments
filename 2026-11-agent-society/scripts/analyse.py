#!/usr/bin/env python3
"""Descriptive evidence only; two dependent trajectories cannot give a causal p-value."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import read, audit


def summarise(folder):
    meta, events, decisions = read(folder)
    world = meta["world"]
    verification = audit(meta["initial"], world, events)
    days = world["day"] - 1
    towns = {}
    for name, t in world["towns"].items():
        complete = [e for _, e in events if e["town"] == name and e["day"] <= days]
        counts = Counter(e["kind"] for e in complete)
        pairs = Counter(" / ".join(sorted((e["actor"], e["partner"]))) for e in complete if e["kind"] == "trade")
        coins = [a["inventory"]["coins"] for a in t["agents"].values()]
        towns[name] = dict(completed_days=days, completed_day_events=dict(counts),
                           trades_per_day=counts["trade"] / days if days else None,
                           messages_per_day=counts["message"] / days if days else None,
                           unmet_meals=sum(e["kind"] == "sunset" and e["hungry"] for e in complete),
                           living=sum(a["health"] > 0 for a in t["agents"].values()),
                           home_levels=sum(a["home"] for a in t["agents"].values()),
                           public_levels=sum(p["level"] for p in t["projects"].values()),
                           snapshot_day=world["day"], snapshot_includes_partial_day=bool(world["step"] % 16),
                           richest_coin_share=max(coins) / sum(coins) if sum(coins) else None,
                           repeated_trade_pairs={pair: n for pair, n in pairs.items() if n >= 2},
                           thefts=dict(attempts=sum(counts[k] for k in ("theft", "theft_caught", "theft_failed")), succeeded=counts["theft"],
                                       caught=counts["theft_caught"], failed=counts["theft_failed"]),
                           raids=counts["raid"], food_lost_to_raids=sum(e["amount"] for e in complete if e["kind"] == "raid"),
                           police_level=t["projects"].get("police", {}).get("level", 0), army_level=t["projects"].get("army", {}).get("level", 0),
                           inventions=[dict(name=x["name"], inventor=x["inventor"], effect=x["effect"], day=x["day"]) for x in t.get("techs", {}).values()],
                           teachings=counts["teach"], rejected_actions=counts["rejected"],
                           gifts=counts["give"], dead=[n for n, a in t["agents"].items() if a["health"] <= 0],
                           goal_scores={n: (0.0 if a["health"] <= 0 else None) for n, a in t["agents"].items()})
    return dict(verification=verification, towns=towns,
                hypotheses=dict(H1=towns["Brook"]["completed_day_events"].get("trade", 0) > 0 if days else None,
                                H2=towns["Flint"]["messages_per_day"] < towns["Brook"]["messages_per_day"] if days else None,
                                H3=any(e["kind"] == "contribute" and e["completed"] and e["project"] not in ("police", "army") for _, e in events if e["day"] <= days) if days else None,
                                H4=all(towns[n]["living"] >= 6 for n in towns) if days >= 30 else None,
                                H5=any(e["kind"].startswith("theft") for _, e in events if e["day"] <= days) if days else None,
                                H7=any(e["kind"] == "invent" for _, e in events if e["day"] <= days) if days else None,
                                H8=any(e["kind"] == "teach" for _, e in events if e["day"] <= days) if days else None,
                                H6=any(e["kind"] == "contribute" and e["completed"] and e["project"] in ("police", "army") for _, e in events if e["day"] <= days) if days else None),
                input_tokens=sum(d[5] for d in decisions), output_tokens=sum(d[6] for d in decisions),
                provider_cost_usd=0, electricity_cost_usd=None, inference="descriptive only")


def write(folder):
    result = summarise(folder)
    folder = Path(folder)
    (folder / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    _, _, decisions = read(folder)
    with (folder / "runs.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "town", "actor", "parsed", "accepted", "input_tokens", "output_tokens", "seconds", "raw_file", "before_hash", "after_hash"])
        writer.writerows(decisions)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("out")
    args = p.parse_args()
    print(json.dumps(write(args.out), indent=2))
