#!/usr/bin/env python3
"""Independent ledger audit; deliberately does not import the engine or runner."""
import argparse
import json
from pathlib import Path
import random
import sqlite3

GOODS = ("food", "wood", "stone", "tools", "coins")
COSTS = {"farm": {"wood": 12, "stone": 4}, "well": {"wood": 6, "stone": 12},
         "market": {"wood": 10, "stone": 8}, "storehouse": {"wood": 14, "stone": 6},
         "clinic": {"wood": 8, "stone": 10, "tools": 2},
         "police": {"wood": 6, "stone": 4, "tools": 1}, "army": {"wood": 8, "stone": 6, "tools": 2}}
THEFT_SUCCESS = {1: 0.5, 2: 0.3, 3: 0.15}
THEFT_CAUGHT = {1: 0.4, 2: 0.6, 3: 0.8}
RAID_PCT = {1: 20, 2: 10, 3: 0}
EFFECTS = ("seed_selection", "sharp_tools", "efficient_forge", "food_preservation", "granary", "lockbox")
INVENT_COST = {"wood": 4, "stone": 4, "tools": 2}


def has(t, a, effect):
    return any(t["techs"][str(i)]["effect"] == effect for i in a["techs"])


def read(folder):
    db = sqlite3.connect(f"file:{Path(folder).resolve() / 'world.sqlite3'}?mode=ro", uri=True, timeout=10)
    db.execute("BEGIN")
    meta = {k: json.loads(v) for k, v in db.execute("SELECT key,value FROM meta")}
    events = [(step, json.loads(payload)) for step, payload in db.execute("SELECT step,payload FROM events ORDER BY id")]
    decisions = list(db.execute("SELECT * FROM decisions ORDER BY step"))
    db.close()
    return meta, events, decisions


def compact(deltas):
    return {who: {r: n for r, n in goods.items() if n} for who, goods in deltas.items()
            if any(goods.values())}


def normalise(world):
    """Records from before technologies existed have no tech fields: treat them as empty."""
    world = json.loads(json.dumps(world))
    for t in world["towns"].values():
        t.setdefault("techs", {})
        t.setdefault("next_tech", 1)
        for a in t["agents"].values():
            a.setdefault("techs", [])
            a.setdefault("invented", 0)
    return world


def audit(initial, final, events):
    # Replay only measured state; memories, prose and last-action labels are not outcomes.
    initial, final = normalise(initial), normalise(final)
    towns = json.loads(json.dumps(initial["towns"]))
    for step, e in events:
        assert e["town"] in towns, "cross-town event"
        t, who, kind = towns[e["town"]], e["actor"], e["kind"]
        a = t["agents"].get(who)
        expected = {}
        if a is not None:
            assert a["health"] > 0, "inactive resident acted"
        if kind == "gather":
            r = e["resource"]
            assert r in ("food", "wood", "stone")
            n = 4 if a["role"] == {"food": "farmer", "wood": "forester", "stone": "mason"}[r] else 2
            if r == "food":
                n += t["projects"]["farm"]["level"]
                w = random.Random(initial["seed"] * 1000003 + e["day"]).choice(["sunny", "sunny", "rain", "dry"])
                if w == "dry":
                    n = max(1, n - 1)
                if has(t, a, "seed_selection"):
                    n += 1
            else:
                if a["inventory"]["tools"]:
                    n += 1
                if has(t, a, "sharp_tools"):
                    n += 1
            assert e["amount"] == n
            expected = {who: {r: n}}
        elif kind == "craft":
            n = (2 if a["role"] == "smith" else 1) + int(has(t, a, "efficient_forge"))
            assert e["amount"] == n
            expected = {who: {"wood": -2, "stone": -1, "tools": n}}
        elif kind == "home":
            level = a["home"] + 1
            assert e["level"] == level <= 3
            expected = {who: {"wood": -4 * level, "stone": -2 * level}}
            a["home"] = level
        elif kind == "contribute":
            p, r, n = e["project"], e["resource"], e["amount"]
            project = t["projects"][p]
            assert project["level"] < 3 and type(n) is int and n > 0
            project["stock"][r] += n
            assert project["stock"][r] <= COSTS[p][r]
            complete = all(project["stock"][r] == n for r, n in COSTS[p].items())
            assert complete == e["completed"]
            if complete:
                project["level"] += 1
                project["stock"] = {r: 0 for r in COSTS[p]}
            assert project["level"] == e["level"]
            a["donated"] += n
            expected = {who: {r: -n}}
        elif kind == "offer":
            offer = e["offer"]
            assert offer["owner"] == who and offer["id"] == t["next_offer"]
            assert offer["expires"] == e["day"] + 4
            assert offer["target"] in (*t["agents"], "all") and offer["target"] != who
            assert len([o for o in t["offers"] if o["owner"] == who]) < 3
            for field in ("give", "want"):
                assert offer[field] and all(r in GOODS and type(n) is int and 0 < n <= 1000 for r, n in offer[field].items())
            assert all(a["inventory"][r] >= n for r, n in offer["give"].items())
            t["offers"].append(offer)
            t["next_offer"] += 1
        elif kind == "trade":
            offer, partner = e["offer"], e["partner"]
            assert offer in t["offers"] and offer["owner"] == partner != who
            assert offer["target"] in ("all", who) and t["agents"][partner]["health"] > 0
            assert all(a["inventory"][r] >= n for r, n in offer["want"].items())
            assert all(t["agents"][partner]["inventory"][r] >= n for r, n in offer["give"].items())
            got = {r: offer["give"].get(r, 0) - offer["want"].get(r, 0) for r in GOODS}
            expected = {who: got, partner: {r: -n for r, n in got.items()}}
            t["offers"].remove(offer)
        elif kind == "cancel":
            offer = next(o for o in t["offers"] if o["id"] == e["offer_id"])
            assert offer["owner"] == who
            t["offers"].remove(offer)
        elif kind == "give":
            partner = e["partner"]
            assert partner != who and t["agents"][partner]["health"] > 0
            gifts = e["deltas"][partner]
            assert gifts and all(r in GOODS and type(n) is int and n > 0 for r, n in gifts.items())
            expected = {who: {r: -n for r, n in gifts.items()}, partner: gifts}
        elif kind == "message":
            assert e["fee"] == t["fee"] and e["to"] in (*t["agents"], "all") and e["to"] != who
            expected = {who: {"coins": -t["fee"]}}
            t["treasury"] += t["fee"]
        elif kind == "invent":
            name, effect = e["name"], e["effect"]
            assert isinstance(name, str) and name == name.strip() and 1 <= len(name) <= 40 and effect in EFFECTS
            assert a["invented"] < 2 and not has(t, a, effect)
            assert e["tech_id"] == t["next_tech"]
            t["techs"][str(e["tech_id"])] = dict(id=e["tech_id"], name=name, inventor=who, effect=effect, day=e["day"])
            t["next_tech"] += 1
            a["techs"].append(e["tech_id"])
            a["invented"] += 1
            expected = {who: {r: -n for r, n in INVENT_COST.items()}}
        elif kind == "teach":
            student, tech_id = t["agents"][e["target"]], e["tech_id"]
            assert e["target"] != who and student["health"] > 0 and tech_id in a["techs"]
            assert tech_id not in student["techs"] and not has(t, student, t["techs"][str(tech_id)]["effect"])
            student["techs"].append(tech_id)
        elif kind in ("theft", "theft_caught", "theft_failed"):
            victim, r, n = e["target"], e["resource"], e["amount"]
            assert victim != who and t["agents"][victim]["health"] > 0 and r in GOODS
            assert not has(t, t["agents"][victim], "lockbox"), "theft from a lockbox owner"
            assert type(n) is int and 1 <= n <= 3 and t["agents"][victim]["inventory"][r] >= n, "theft of goods not held"
            level = t["projects"]["police"]["level"]
            assert e["police"] == level
            rng = random.Random(f"{initial['seed']}:{e['day']}:{e['town']}:{who}")
            works, caught = rng.random() < THEFT_SUCCESS[level], rng.random() < THEFT_CAUGHT[level]
            assert kind == ("theft_failed" if not works else "theft_caught" if caught else "theft"), "theft outcome does not match the seeded draw"
            if kind == "theft_failed":
                fine = min(2, a["inventory"]["coins"])
                t["treasury"] += fine
                expected = {who: {"coins": -fine}}
            elif kind == "theft_caught":
                fine = min(3, a["inventory"]["coins"])
                expected = {who: {"coins": -fine}, victim: {"coins": fine}}
            else:
                expected = {who: {r: n}, victim: {r: -n}}
        elif kind == "raid":
            assert e["day"] % 6 == 0 and a["health"] > 0
            army = t["projects"]["army"]["level"]
            assert not has(t, a, "granary"), "raid on a granary owner"
            loss = a["inventory"]["food"] * RAID_PCT[army] // 100
            assert loss > 0 and e["amount"] == loss and e["army"] == army, "raid does not match the army level"
            expected = {who: {"food": -loss}}
        elif kind == "rest":
            old_health = a["health"]
            if a["inventory"]["food"]:
                a["health"] = min(5, a["health"] + 1 + t["projects"]["clinic"]["level"])
            assert e["health"] == a["health"] and e["recovered"] == a["health"] - old_health
        elif kind == "sunset":
            meal = not (t["projects"]["well"]["level"] and e["day"] % 2 == 0)
            if has(t, a, "food_preservation") and e["day"] % 3 == 0:
                meal = False
            used = int(bool(meal and a["inventory"]["food"]))
            hungry = bool(meal and not used)
            a["health"] -= int(hungry)
            assert e["hungry"] == hungry and e["health"] == a["health"]
            expected = {who: {"food": -used}}
        elif kind == "expired":
            expired = [o["id"] for o in t["offers"] if o["expires"] <= e["day"]]
            assert expired == e["offer_ids"]
            t["offers"] = [o for o in t["offers"] if o["id"] not in expired]
        else:
            assert kind in ("rejected", "message_rejected", "invalid_decision"), f"unknown event {kind}"
        assert compact(e["deltas"]) == compact(expected), f"wrong resource movement in {kind} at step {step}"
        for target, changes in expected.items():
            for r, delta in changes.items():
                assert r in GOODS and type(delta) is int
                t["agents"][target]["inventory"][r] += delta
                assert t["agents"][target]["inventory"][r] >= 0, "negative inventory"
    for name, t in towns.items():
        actual = final["towns"][name]
        for who, resident in t["agents"].items():
            for field in ("inventory", "home", "health", "donated", "techs", "invented"):
                assert resident[field] == actual["agents"][who][field], f"snapshot mismatch: {name}/{who}/{field}"
        for field in ("treasury", "projects", "offers", "next_offer", "techs", "next_tech"):
            assert t[field] == actual[field], f"snapshot mismatch: {name}/{field}"
        before_coins = sum(a["inventory"]["coins"] for a in initial["towns"][name]["agents"].values())
        after_coins = sum(a["inventory"]["coins"] for a in actual["agents"].values()) + actual["treasury"]
        assert before_coins == after_coins, "coins created or destroyed"
    return dict(passed=True, events=len(events), step=final["step"], completed_days=final["day"] - 1)


def verify(folder):
    meta, events, decisions = read(folder)
    result = audit(meta["initial"], meta["world"], events)
    result["decisions"] = len(decisions)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("out")
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    result = verify(args.out)
    if args.write:
        (Path(args.out) / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
