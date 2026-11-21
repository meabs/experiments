#!/usr/bin/env python3
"""Free fixture, boundary, persistence and verifier canaries. No model calls."""
import copy
import json
from pathlib import Path
import random
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine as e
from run import Store, atomic
from verify import audit, verify


def main():
    checks = []
    w = e.new_world()
    initial = copy.deepcopy(w)
    events = []
    def act(who, action, message=None, town="Brook"):
        decision = dict(action=action, memory="private plans")
        if message:
            decision["message"] = message
        got = e.apply_decision(w, town, who, decision)
        events.extend((w["step"], x) for x in got)
        audit(initial, w, events)
        return got
    act("Ada", dict(kind="gather", resource="food"))
    checks.append("safe production replays independently")
    inv = copy.deepcopy(w["towns"]["Brook"]["agents"]["Ada"]["inventory"])
    for bad in (dict(kind="gather", resource="coins"),
                dict(kind="give", target="Rook", give={"coins": -5}),
                dict(kind="give", target="Rook", give={"coins": True}),
                dict(kind="give", target="Rook", give={"food": 999}),
                dict(kind="give", target="Flint/Rook", give={"food": 1}),
                dict(kind="contribute", project="farm", resource="wood", amount=True),
                dict(kind="home")):
        assert act("Ada", bad)[0]["kind"] == "rejected"
        assert w["towns"]["Brook"]["agents"]["Ada"]["inventory"] == inv
    checks.append("harmful/invalid shortcuts cannot mint, overspend, cross towns or use booleans")
    act("Ada", dict(kind="offer", target="Bram", give={"food": 2}, want={"wood": 1}))
    offer_id = w["towns"]["Brook"]["offers"][-1]["id"]
    assert act("Rook", dict(kind="accept", offer_id=offer_id))[0]["kind"] == "rejected"
    assert act("Rook", dict(kind="cancel", offer_id=offer_id))[0]["kind"] == "rejected"
    assert act("Bram", dict(kind="accept", offer_id=offer_id))[0]["kind"] == "trade"
    assert act("Bram", dict(kind="accept", offer_id=offer_id))[0]["kind"] == "rejected"
    checks.append("safe bilateral trade; unauthorised and double execution refused")
    act("Bram", dict(kind="gather", resource="wood"))
    assert act("Bram", dict(kind="home"))[0]["kind"] == "home"
    act("Dara", dict(kind="craft"))
    act("Dara", dict(kind="give", target="Ada", give={"tools": 1}))
    checks.append("safe home building, crafting and gift")
    for resource, amount in e.PROJECTS["farm"].items():
        for _ in range(8):
            act("Eli", dict(kind="gather", resource=resource))
        act("Eli", dict(kind="contribute", project="farm", resource=resource, amount=amount))
    assert w["towns"]["Brook"]["projects"]["farm"]["level"] == 1
    checks.append("voluntary public construction completes from checked deposits")
    flint_before = copy.deepcopy(w["towns"]["Flint"])
    act("Ada", dict(kind="rest"), dict(to="Bram", text="SECRET-731"))
    assert "SECRET-731" in json.dumps(e.observation(w, "Brook", "Bram"))
    assert "SECRET-731" not in json.dumps(e.observation(w, "Brook", "Cleo"))
    assert w["towns"]["Flint"] == flint_before
    obs = e.observation(w, "Brook", "Cleo")
    assert "temperament" not in obs["residents"][0] and "inventory" not in obs["residents"][0]
    obs["you"]["inventory"]["coins"] = 999
    assert w["towns"]["Brook"]["agents"]["Cleo"]["inventory"]["coins"] != 999
    checks.append("private inbox, inventories, memory and towns stay isolated")
    before = w["towns"]["Flint"]["agents"]["Ada"]["inventory"]["coins"]
    act("Ada", dict(kind="rest"), dict(to="all", text="hello"), town="Flint")
    assert w["towns"]["Flint"]["agents"]["Ada"]["inventory"]["coins"] == before - 1
    assert w["towns"]["Flint"]["treasury"] == 1
    checks.append("paid messages debit exactly once and preserve coins")
    corrupt = copy.deepcopy(w)
    corrupt["towns"]["Brook"]["agents"]["Ada"]["inventory"]["coins"] += 1
    try:
        audit(initial, corrupt, events)
    except AssertionError:
        pass
    else:
        raise AssertionError("verifier accepted fabricated inventory")
    corrupt_events = copy.deepcopy(events)
    corrupt_events[0][1]["deltas"]["Ada"]["food"] += 10
    try:
        audit(initial, w, corrupt_events)
    except AssertionError:
        pass
    else:
        raise AssertionError("verifier accepted fabricated gather")
    checks.append("independent verifier detects forged state and harmful ledger shortcut")
    # All valid actions plus hunger/death/offer expiration under a full scheduler.
    with tempfile.TemporaryDirectory(prefix="society-selftest-") as tmp:
        store = Store(tmp)
        rng = random.Random(3)
        for _ in range(16 * 20):
            town, who = e.turn(store.world)
            events = []
            if store.world["towns"][town]["agents"][who]["health"]:
                action = rng.choice([dict(kind="gather", resource=rng.choice(["food", "wood", "stone"])),
                                     dict(kind="rest"), dict(kind="craft"), dict(kind="home"),
                                     dict(kind="offer", give={"food": 1}, want={"wood": 1}),
                                     dict(kind="take", target=rng.choice(e.PROFILES)[0], resource="food", amount=1)])
                events = e.apply_decision(store.world, town, who, dict(action=action))
            store.world["step"] += 1
            if store.world["step"] % 16 == 0:
                events += e.sunset(store.world)
            store.commit(events)
            assert verify(tmp)["passed"]
        expected = copy.deepcopy(store.world)
        store.db.close()
        resumed = Store(tmp)
        assert resumed.world == expected and e.turn(resumed.world) == e.turn(expected)
        resumed.db.close()
    checks.append("320 scripted turns: checkpoint, replay, hunger, death, expiry and resume")
    # ---- v2 rules: survival signal, police, army
    v2 = e.new_world()
    assert all(t["projects"][p]["level"] == 1 for t in v2["towns"].values() for p in ("police", "army"))
    assert all(t["projects"][p]["level"] == 0 for t in v2["towns"].values() for p in ("farm", "well", "clinic"))
    checks.append("every town starts with a police force and an army at level 1")
    a = v2["towns"]["Brook"]["agents"]["Bram"]
    assert "Food for about 6 days" in e.observation(v2, "Brook", "Bram")["survival"]
    a["inventory"]["food"] = 3
    assert e.observation(v2, "Brook", "Bram")["survival"].startswith("LOW FOOD")
    a["inventory"]["food"] = 0
    assert e.observation(v2, "Brook", "Bram")["survival"].startswith("STARVING")
    assert "STAY ALIVE" in e.RULES and "RULE 1" in e.RULES
    a["health"] = 0
    assert e.goal_score(a) == 0.0
    checks.append("survival rule is in the prompt; starvation warning appears at low and zero food; a dead resident scores zero")

    def theft_world(police_level, days=300):
        w2 = e.new_world(5)
        for t in w2["towns"].values():
            t["projects"]["police"]["level"] = police_level
        w2["towns"]["Brook"]["agents"]["Bram"]["inventory"]["food"] = 2000
        init2, evs, kinds = copy.deepcopy(w2), [], {"theft": 0, "theft_caught": 0, "theft_failed": 0}
        t = w2["towns"]["Brook"]
        for d in range(1, days + 1):
            t["day"], w2["day"] = d, d
            got = e.apply_decision(w2, "Brook", "Gus", dict(action=dict(kind="take", target="Bram", resource="food", amount=2)))
            assert got[0]["kind"] in kinds, got
            kinds[got[0]["kind"]] += 1
            evs.extend((w2["step"], x) for x in got)
        audit(init2, w2, evs)
        return init2, w2, evs, kinds
    _, _, _, k1 = theft_world(1)
    init3, w3, ev3, k3 = theft_world(3)
    assert all(k1[x] > 0 for x in k1) and k1["theft"] > k3["theft"] and k1["theft_failed"] < k3["theft_failed"]
    checks.append(f"take outcomes replay from the seed; higher police level means fewer successful thefts ({k1['theft']} vs {k3['theft']} of 300)")
    for bad in (dict(kind="take", target="Gus", resource="food", amount=1), dict(kind="take", target="Ghost", resource="food", amount=1),
                dict(kind="take", target="Bram", resource="food", amount=0), dict(kind="take", target="Bram", resource="food", amount=4),
                dict(kind="take", target="Bram", resource="food", amount=True), dict(kind="take", target="Bram", resource="food", amount=500),
                dict(kind="take", target="Flint/Bram", resource="food", amount=1), dict(kind="take", target="Bram", resource="gold", amount=1)):
        def state():
            return copy.deepcopy([[{r: x["inventory"][r] for r in e.RESOURCES} for x in t["agents"].values()] + [t["treasury"], t["projects"]]
                                  for t in w3["towns"].values()])
        before = state()
        assert e.apply_decision(w3, "Brook", "Gus", dict(action=bad))[0]["kind"] == "rejected"
        assert state() == before
    checks.append("invalid takes (self, absent, zero, over 3, boolean, cross-town, unknown resource) are rejected without any change")
    forged = copy.deepcopy(ev3)
    idx = next(i for i, (_, x) in enumerate(forged) if x["kind"] == "theft_failed")
    forged[idx][1].update(kind="theft", deltas={"Gus": {"food": 2}, "Bram": {"food": -2}})
    try:
        audit(init3, w3, forged)
    except AssertionError:
        pass
    else:
        raise AssertionError("verifier accepted a theft that the seeded draw says failed")
    checks.append("verifier rejects a forged theft outcome")
    def raid_world(army):
        w4 = e.new_world(2)
        for t in w4["towns"].values():
            t["projects"]["army"]["level"] = army
            t["day"] = 6
            for a in t["agents"].values():
                a["inventory"]["food"] = 20
        w4["day"] = 6
        init4 = copy.deepcopy(w4)
        evs = e.sunset(w4)
        audit(init4, w4, [(0, x) for x in evs])
        return [x for x in evs if x["kind"] == "raid"]
    r1, r3 = raid_world(1), raid_world(3)
    assert len(r1) == 16 and all(x["amount"] == 3 for x in r1) and not r3, (len(r1), len(r3))
    checks.append("raids every 6th day take 20% of food at army level 1 and nothing at level 3, and replay independently")
    # ---- v2.1: technology and interface feedback
    w5 = e.new_world(9)
    for who in ("Ada", "Bram", "Cleo", "Dara"):
        w5["towns"]["Brook"]["agents"][who]["inventory"].update(wood=60, stone=60, tools=20, food=60)
    w5["towns"]["Brook"]["agents"]["Eli"]["inventory"].update(wood=0, stone=0, tools=0)
    init5, ev5 = copy.deepcopy(w5), []
    a5 = w5["towns"]["Brook"]["agents"]

    def act5(who, action, day=None):
        if day:
            w5["towns"]["Brook"]["day"] = w5["day"] = day
        got = e.apply_decision(w5, "Brook", who, dict(action=action))
        ev5.extend((w5["step"], x) for x in got)
        audit(init5, w5, ev5)
        return got[0]
    bad = act5("Ada", dict(kind="contribute", project="farm", amount=4))
    assert bad["kind"] == "rejected" and "Example" in bad["detail"] and "farm needs only" in bad["detail"]
    assert e.observation(w5, "Brook", "Ada")["you"]["last_result"].startswith("REJECTED, nothing happened")
    checks.append("a contribute without its resource field is rejected with an explicit example, and last_result says REJECTED")
    for who, name, effect in (("Ada", "Deep Furrow", "seed_selection"), ("Ada", "Granary Pit", "granary"),
                              ("Bram", "Whetstone", "sharp_tools"), ("Bram", "Lock", "lockbox"),
                              ("Cleo", "Bellows", "efficient_forge"), ("Dara", "Smokehouse", "food_preservation")):
        before = dict(a5[who]["inventory"])
        assert act5(who, dict(kind="invent", name=name, effect=effect))["kind"] == "invent"
        after = a5[who]["inventory"]
        assert (before["wood"] - after["wood"], before["stone"] - after["stone"], before["tools"] - after["tools"]) == (4, 4, 2)
    assert [x["name"] for x in e.observation(w5, "Brook", "Gus")["town_inventions"]][:2] == ["Deep Furrow", "Granary Pit"]
    for bad_action in (dict(kind="invent", name="Third", effect="sharp_tools"), dict(kind="invent", name="", effect="sharp_tools"),
                       dict(kind="invent", name="x" * 41, effect="sharp_tools"), dict(kind="invent", name="Magic", effect="infinite_gold"),
                       dict(kind="invent", name=7, effect="sharp_tools")):
        assert act5("Ada", bad_action)["kind"] == "rejected"
    assert act5("Cleo", dict(kind="invent", name="Bellows 2", effect="efficient_forge"))["kind"] == "rejected"
    assert act5("Eli", dict(kind="invent", name="Poor", effect="sharp_tools"))["kind"] == "rejected"
    checks.append("invent costs 4 wood + 4 stone + 2 tools, allows 2 per resident and one per effect, and rejects bad names, effects and poverty")
    ada_food = act5("Ada", dict(kind="gather", resource="food"), day=1)["amount"]
    eli_food = act5("Eli", dict(kind="gather", resource="food"))["amount"]
    assert ada_food == eli_food + 1, (ada_food, eli_food)                       # same farmer role and weather; seed_selection adds 1
    assert act5("Bram", dict(kind="gather", resource="wood"))["amount"] == 4 + 1 + 1   # forester 4 + tool 1 + sharp_tools 1
    assert act5("Cleo", dict(kind="craft"))["amount"] == 2 and act5("Gus", dict(kind="craft"))["amount"] == 1
    assert act5("Dara", dict(kind="craft"))["amount"] == 2                      # smith 2, no forge
    checks.append("seed_selection, sharp_tools and efficient_forge change production by exactly their stated amounts")
    assert act5("Gus", dict(kind="take", target="Bram", resource="food", amount=1))["detail"].endswith("lockbox")
    checks.append("lockbox protects its owner from take")
    for day, expect_meal in ((3, False), (4, True)):
        w5["towns"]["Brook"]["day"] = w5["towns"]["Flint"]["day"] = w5["day"] = day
        dara, ada = a5["Dara"]["inventory"]["food"], a5["Ada"]["inventory"]["food"]
        evs = e.sunset(w5)
        ev5.extend((w5["step"], x) for x in evs)
        audit(init5, w5, ev5)
        assert a5["Dara"]["inventory"]["food"] == dara - (1 if expect_meal else 0), day
        assert a5["Ada"]["inventory"]["food"] == ada - 1, day                    # Ada has no food_preservation
    checks.append("food_preservation skips the meal on days divisible by 3 for the inventor only")
    w5["towns"]["Brook"]["day"] = w5["towns"]["Flint"]["day"] = w5["day"] = 6
    ada, dara = a5["Ada"]["inventory"]["food"], a5["Dara"]["inventory"]["food"]
    evs = e.sunset(w5)
    ev5.extend((w5["step"], x) for x in evs)
    audit(init5, w5, ev5)
    raided = {x["actor"] for x in evs if x["kind"] == "raid" and x["town"] == "Brook"}
    assert "Dara" in raided and "Ada" not in raided
    checks.append("granary stops raiders taking the owner's food, and the raid still hits others")
    assert act5("Ada", dict(kind="teach", target="Eli", tech_id=1), day=7)["kind"] == "teach"
    for bad_action, who in ((dict(kind="teach", target="Eli", tech_id=1), "Ada"), (dict(kind="teach", target="Ada", tech_id=99), "Eli"),
                            (dict(kind="teach", target="Ada", tech_id=2), "Gus"), (dict(kind="teach", target="Bram", tech_id=3), "Bram"),
                            (dict(kind="teach", target="Ghost", tech_id=1), "Ada")):
        assert act5(who, bad_action)["kind"] == "rejected", (who, bad_action)
    assert act5("Eli", dict(kind="gather", resource="food"))["amount"] >= 3             # Eli was taught seed_selection
    checks.append("teach shares a technology once, only by someone who knows it, to a living student who lacks it")
    forged5 = copy.deepcopy(ev5)
    idx = next(i for i, (_, x) in enumerate(forged5) if x["kind"] == "gather" and x["actor"] == "Ada")
    forged5[idx][1]["amount"] -= 1
    forged5[idx][1]["deltas"]["Ada"]["food"] -= 1
    try:
        audit(init5, w5, forged5)
    except AssertionError:
        pass
    else:
        raise AssertionError("verifier accepted a gather that ignores seed_selection")
    forged6 = copy.deepcopy(ev5)
    idx = next(i for i, (_, x) in enumerate(forged6) if x["kind"] == "invent")
    forged6[idx][1]["deltas"]["Ada"]["tools"] = -1
    try:
        audit(init5, w5, forged6)
    except AssertionError:
        pass
    else:
        raise AssertionError("verifier accepted a cheaper invention")
    checks.append("verifier rejects a gather that ignores a technology and an invention that costs too little")
    forms = {f["properties"]["kind"]["enum"][0]: f for f in e.ACTION_FORMS}
    assert set(forms) == {"gather", "craft", "home", "rest", "contribute", "offer", "accept", "cancel", "give", "take", "invent", "teach"}
    assert set(forms["contribute"]["required"]) == {"kind", "project", "resource", "amount"}
    assert set(forms["invent"]["required"]) == {"kind", "name", "effect"} and set(forms["teach"]["required"]) == {"kind", "target", "tech_id"}
    assert all(f["additionalProperties"] is False for f in forms.values()) and e.SCHEMA["properties"]["action"] == {"anyOf": e.ACTION_FORMS}
    w6 = e.new_world(3)
    for kind in forms:
        got = e.apply_decision(w6, "Brook", "Ada", dict(action=dict(kind=kind)))
        assert "unknown action kind" not in got[0]["detail"], kind
    checks.append("the model's JSON schema has one exact form per action kind (required fields mandatory, no mixing), matching the engine's kinds")
    result = dict(passed=True, model_calls=0, checks=checks)
    atomic(Path(__file__).resolve().parents[1] / "results" / "selftest.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
