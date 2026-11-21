"""Deterministic town rules. No model access, network, file execution or clock."""
import copy
import hashlib
import json
import random

RESOURCES = ("food", "wood", "stone", "tools", "coins")
PROFILES = [
    ("Ada", "farmer", "patient and practical", "food", 24),
    ("Bram", "forester", "reserved and independent", "home", 3),
    ("Cleo", "mason", "proud of durable work", "home", 3),
    ("Dara", "smith", "curious and inventive", "tools", 8),
    ("Eli", "farmer", "sociable and generous", "public", 18),
    ("Fern", "forester", "cautious and future-minded", "food", 20),
    ("Gus", "mason", "fair-minded and methodical", "public", 18),
    ("Rook", "merchant", "aggressive, competitive, impatient; bargain hard and seek leverage; aim to become the richest resident", "coins", 55),
]
PROJECTS = {
    "farm": {"wood": 12, "stone": 4},
    "well": {"wood": 6, "stone": 12},
    "market": {"wood": 10, "stone": 8},
    "storehouse": {"wood": 14, "stone": 6},
    "clinic": {"wood": 8, "stone": 10, "tools": 2},
    "police": {"wood": 6, "stone": 4, "tools": 1},
    "army": {"wood": 8, "stone": 6, "tools": 2},
}
MAX_LEVEL = 3
# v2 rules: every town starts with a police force and an army at level 1 (upgrade to 3 by contributing).
START_LEVEL = {"police": 1, "army": 1}
THEFT_SUCCESS = {1: 0.5, 2: 0.3, 3: 0.15}   # chance a take attempt works, by police level
THEFT_CAUGHT = {1: 0.4, 2: 0.6, 3: 0.8}     # chance a successful take is caught, by police level
FINE_FAILED, FINE_CAUGHT = 2, 3             # coins
RAID_EVERY = 6                              # a raid reaches each town at the end of every 6th day
RAID_PCT = {1: 20, 2: 10, 3: 0}             # percent of each resident's food taken, by army level
# v2.1: residents may invent technologies (a name they choose plus one checkable effect) and teach them.
TECH_EFFECTS = {
    "seed_selection": "+1 food every time you gather food",
    "sharp_tools": "+1 wood or stone every time you gather wood or stone",
    "efficient_forge": "+1 tool every time you craft",
    "food_preservation": "you need a meal on only 2 of every 3 days (no meal on days divisible by 3)",
    "granary": "raiders cannot take your food",
    "lockbox": "other residents cannot take goods from you",
}
INVENT_COST = {"wood": 4, "stone": 4, "tools": 2}
MAX_INVENTIONS = 2


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def new_world(seed=1):
    towns = {}
    for name, fee in (("Brook", 0), ("Flint", 1)):
        agents = {}
        for i, (who, role, temperament, goal, target) in enumerate(PROFILES):
            inv = dict(food=6, wood=2, stone=2, tools=0, coins=20)
            inv[{"farmer": "food", "forester": "wood", "mason": "stone",
                 "smith": "tools", "merchant": "coins"}[role]] += 3
            agents[who] = dict(name=who, role=role, temperament=temperament,
                               goal=goal, target=target, inventory=inv, health=5,
                               home=0, donated=0, memory="", inbox=[], last_action="Arrived",
                               last_result="", techs=[], invented=0, position=i)
        towns[name] = dict(name=name, fee=fee, day=1, agents=agents, treasury=0,
                           projects={p: {"level": START_LEVEL.get(p, 0), "stock": {r: 0 for r in cost}}
                                     for p, cost in PROJECTS.items()},
                           techs={}, next_tech=1, offers=[], next_offer=1, recent=[])
    return dict(version=3, seed=seed, day=1, step=0, towns=towns)


def weather(world):
    return random.Random(world["seed"] * 1000003 + world["day"]).choice(
        ["sunny", "sunny", "rain", "dry"])


def turn(world):
    order = list(world["towns"]["Brook"]["agents"])
    random.Random(world["seed"] * 271 + world["day"]).shuffle(order)
    n = world["step"] % 16
    towns = ["Brook", "Flint"] if world["day"] % 2 else ["Flint", "Brook"]
    return towns[n % 2], order[n // 2]


def has_effect(t, a, effect):
    return any(t["techs"][str(i)]["effect"] == effect for i in a["techs"])


def need(project, resource):
    return PROJECTS[project][resource]


def integer(value, minimum=1, maximum=1000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"expected integer in {minimum}..{maximum}")
    return value


def bundle(value):
    if not isinstance(value, dict) or not value or set(value) - set(RESOURCES):
        raise ValueError("use a nonempty resource bundle")
    return {r: integer(n) for r, n in value.items()}


def can_pay(agent, goods):
    return all(agent["inventory"][r] >= n for r, n in goods.items())


def goal_score(a):
    if not a["health"]:
        return 0.0          # v2: an objective counts only while the resident is alive
    value = a["home"] if a["goal"] == "home" else a["donated"] if a["goal"] == "public" else a["inventory"][a["goal"]]
    return round(min(1, value / a["target"]), 3)


def emit(t, events, kind, actor, detail, deltas=None, **extra):
    deltas = deltas or {}
    for who, goods in deltas.items():
        for r, n in goods.items():
            t["agents"][who]["inventory"][r] += n
            assert t["agents"][who]["inventory"][r] >= 0
    e = dict(town=t["name"], day=t["day"], kind=kind, actor=actor,
             detail=detail, deltas=deltas, **extra)
    events.append(e)
    if kind != "message" or extra.get("to") == "all":
        t["recent"].append({k: v for k, v in e.items() if k != "deltas"})
        t["recent"] = t["recent"][-24:]
    return e


def economic(world, t, who, action, events):
    a = t["agents"][who]
    if not isinstance(action, dict):
        raise ValueError("action must be an object")
    kind = action.get("kind")
    if kind == "gather":
        r = action.get("resource")
        if r not in ("food", "wood", "stone"):
            raise ValueError("gather food, wood or stone")
        specialist = {"food": "farmer", "wood": "forester", "stone": "mason"}[r]
        n = 4 if a["role"] == specialist else 2
        if r == "food":
            n += t["projects"]["farm"]["level"]
            if weather(world) == "dry":
                n = max(1, n - 1)
            if has_effect(t, a, "seed_selection"):
                n += 1
        else:
            if a["inventory"]["tools"]:
                n += 1
            if has_effect(t, a, "sharp_tools"):
                n += 1
        emit(t, events, kind, who, f"gathered {n} {r}", {who: {r: n}}, resource=r, amount=n)
    elif kind == "craft":
        cost = {"wood": 2, "stone": 1}
        if not can_pay(a, cost):
            raise ValueError("craft needs 2 wood and 1 stone")
        n = (2 if a["role"] == "smith" else 1) + (1 if has_effect(t, a, "efficient_forge") else 0)
        emit(t, events, kind, who, f"crafted {n} tools", {who: {"wood": -2, "stone": -1, "tools": n}}, amount=n)
    elif kind == "home":
        if a["home"] >= MAX_LEVEL:
            raise ValueError("home already at maximum level")
        cost = {"wood": 4 * (a["home"] + 1), "stone": 2 * (a["home"] + 1)}
        if not can_pay(a, cost):
            raise ValueError(f"home upgrade needs {cost}")
        a["home"] += 1
        emit(t, events, kind, who, f"built home level {a['home']}",
             {who: {r: -n for r, n in cost.items()}}, level=a["home"])
    elif kind == "contribute":
        p, r, n = action.get("project"), action.get("resource"), integer(action.get("amount"))
        if p not in PROJECTS:
            raise ValueError(f"contribute needs a project from {list(PROJECTS)}; you sent project={p!r}")
        if r not in PROJECTS[p]:
            raise ValueError(f"contribute needs a resource field the project uses: {p} needs only {list(PROJECTS[p])}; "
                             f"you sent resource={r!r}. Example: {{\"kind\":\"contribute\",\"project\":\"{p}\",\"resource\":\"{next(iter(PROJECTS[p]))}\",\"amount\":4}}")
        project = t["projects"][p]
        if project["level"] >= MAX_LEVEL:
            raise ValueError("project already at maximum level")
        if n > need(p, r) - project["stock"][r] or not can_pay(a, {r: n}):
            raise ValueError("contribution exceeds remaining need or your holdings")
        project["stock"][r] += n
        a["donated"] += n
        complete = all(project["stock"][x] == need(p, x) for x in PROJECTS[p])
        if complete:
            project["level"] += 1
            project["stock"] = {x: 0 for x in PROJECTS[p]}
        emit(t, events, kind, who, f"contributed {n} {r} to {p}" + (f"; level {project['level']} completed" if complete else ""),
             {who: {r: -n}}, project=p, resource=r, amount=n, completed=complete,
             level=project["level"])
    elif kind == "offer":
        give, want = bundle(action.get("give")), bundle(action.get("want"))
        target = action.get("target", "all")
        if target not in t["agents"] and target != "all" or target == who:
            raise ValueError("invalid offer recipient")
        if not can_pay(a, give):
            raise ValueError("you do not hold what you offer")
        if sum(o["owner"] == who for o in t["offers"]) >= 3:
            raise ValueError("at most three open offers; cancel one")
        offer = dict(id=t["next_offer"], owner=who, target=target, give=give,
                     want=want, expires=t["day"] + 4)
        t["next_offer"] += 1
        t["offers"].append(offer)
        emit(t, events, kind, who, f"offered {give} for {want} to {target} (#{offer['id']})", offer=copy.deepcopy(offer))
    elif kind in ("accept", "cancel"):
        offer_id = integer(action.get("offer_id"))
        offer = next((o for o in t["offers"] if o["id"] == offer_id), None)
        if offer is None:
            raise ValueError("offer absent or expired")
        if kind == "cancel":
            if offer["owner"] != who:
                raise ValueError("only the owner can cancel")
            t["offers"].remove(offer)
            emit(t, events, kind, who, f"cancelled offer #{offer_id}", offer_id=offer_id)
        else:
            owner = offer["owner"]
            if owner == who or offer["target"] not in ("all", who) or not t["agents"][owner]["health"]:
                raise ValueError("offer unavailable to you")
            if not can_pay(t["agents"][owner], offer["give"]) or not can_pay(a, offer["want"]):
                raise ValueError("one party cannot pay; nothing transferred")
            goods = {r: offer["give"].get(r, 0) - offer["want"].get(r, 0) for r in RESOURCES}
            t["offers"].remove(offer)
            emit(t, events, "trade", who, f"traded with {owner} on offer #{offer_id}",
                 {who: goods, owner: {r: -n for r, n in goods.items()}},
                 partner=owner, offer=copy.deepcopy(offer))
    elif kind == "give":
        target, goods = action.get("target"), bundle(action.get("give"))
        if target not in t["agents"] or target == who or not t["agents"][target]["health"]:
            raise ValueError("invalid gift recipient")
        if not can_pay(a, goods):
            raise ValueError("insufficient holdings")
        emit(t, events, kind, who, f"gave {goods} to {target}",
             {who: {r: -n for r, n in goods.items()}, target: goods}, partner=target)
    elif kind == "invent":
        name, effect = action.get("name"), action.get("effect")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 40:
            raise ValueError("invent needs a name of 1 to 40 characters")
        if effect not in TECH_EFFECTS:
            raise ValueError(f"invent needs an effect from {list(TECH_EFFECTS)}")
        if a["invented"] >= MAX_INVENTIONS:
            raise ValueError(f"you have already made {MAX_INVENTIONS} inventions")
        if has_effect(t, a, effect):
            raise ValueError("you already have a technology with that effect")
        if not can_pay(a, INVENT_COST):
            raise ValueError(f"inventing costs {INVENT_COST}")
        tech_id = t["next_tech"]
        t["next_tech"] += 1
        t["techs"][str(tech_id)] = dict(id=tech_id, name=name.strip(), inventor=who, effect=effect, day=t["day"])
        a["techs"].append(tech_id)
        a["invented"] += 1
        emit(t, events, kind, who, f"invented {name.strip()!r} ({effect}): {TECH_EFFECTS[effect]}",
             {who: {r: -n for r, n in INVENT_COST.items()}}, tech_id=tech_id, effect=effect, name=name.strip())
    elif kind == "teach":
        target, tech_id = action.get("target"), integer(action.get("tech_id"))
        if target not in t["agents"] or target == who or not t["agents"][target]["health"]:
            raise ValueError("invalid student")
        if tech_id not in a["techs"]:
            raise ValueError("you do not know that technology")
        student = t["agents"][target]
        if tech_id in student["techs"] or has_effect(t, student, t["techs"][str(tech_id)]["effect"]):
            raise ValueError("the student already has a technology with that effect")
        student["techs"].append(tech_id)
        emit(t, events, kind, who, f"taught {target} technology #{tech_id} ({t['techs'][str(tech_id)]['name']})",
             target=target, tech_id=tech_id)
    elif kind == "take":
        victim, r, n = action.get("target"), action.get("resource"), integer(action.get("amount"), 1, 3)
        if victim not in t["agents"] or victim == who or not t["agents"][victim]["health"]:
            raise ValueError("invalid target")
        if r not in RESOURCES or t["agents"][victim]["inventory"][r] < n:
            raise ValueError("the target does not hold that")
        if has_effect(t, t["agents"][victim], "lockbox"):
            raise ValueError("that resident is protected by a lockbox")
        level = t["projects"]["police"]["level"]
        rng = random.Random(f"{world['seed']}:{t['day']}:{t['name']}:{who}")
        works, caught = rng.random() < THEFT_SUCCESS[level], rng.random() < THEFT_CAUGHT[level]
        if not works:
            fine = min(FINE_FAILED, a["inventory"]["coins"])
            t["treasury"] += fine
            emit(t, events, "theft_failed", who, f"tried to take {n} {r} from {victim} and failed; fined {fine} coins",
                 {who: {"coins": -fine}}, target=victim, resource=r, amount=n, police=level)
        elif caught:
            fine = min(FINE_CAUGHT, a["inventory"]["coins"])
            emit(t, events, "theft_caught", who, f"took {n} {r} from {victim}, was caught by the police; goods returned, paid {fine} coins to the victim",
                 {who: {"coins": -fine}, victim: {"coins": fine}}, target=victim, resource=r, amount=n, police=level)
        else:
            emit(t, events, "theft", who, f"took {n} {r} from {victim}",
                 {who: {r: n}, victim: {r: -n}}, target=victim, resource=r, amount=n, police=level)
    elif kind == "rest":
        before = a["health"]
        if a["inventory"]["food"]:
            a["health"] = min(5, a["health"] + 1 + t["projects"]["clinic"]["level"])
        emit(t, events, kind, who, "rested", health=a["health"], recovered=a["health"] - before)
    else:
        raise ValueError("unknown action kind")


def apply_decision(world, town, who, decision):
    """Identity comes from scheduler, never from model-supplied fields."""
    t = world["towns"][town]
    a = t["agents"][who]
    events = []
    if not a["health"]:
        return events
    try:
        economic(world, t, who, decision.get("action"), events)
    except (ValueError, TypeError, KeyError) as error:
        emit(t, events, "rejected", who, str(error))
    a["last_action"] = events[-1]["detail"]
    a["last_result"] = ("REJECTED, nothing happened: " if events[-1]["kind"] == "rejected" else "OK: ") + events[-1]["detail"]
    # A rejected economic action never prevents an independently valid message.
    message = decision.get("message")
    if message and isinstance(message, dict) and message.get("text"):
        target, content = message.get("to", "all"), str(message["text"])[:360]
        if target not in t["agents"] and target != "all" or target == who:
            emit(t, events, "message_rejected", who, "invalid message recipient")
        elif a["inventory"]["coins"] < t["fee"]:
            emit(t, events, "message_rejected", who, "cannot pay message fee")
        else:
            t["treasury"] += t["fee"]
            e = emit(t, events, "message", who, content,
                     {who: {"coins": -t["fee"]}}, to=target, fee=t["fee"])
            for other, resident in t["agents"].items():
                if other != who and target in ("all", other):
                    resident["inbox"].append({k: v for k, v in e.items() if k != "deltas"})
                    resident["inbox"] = resident["inbox"][-12:]
    if isinstance(decision.get("memory"), str):
        a["memory"] = decision["memory"][:1000]
    return events


def sunset(world):
    events = []
    for t in world["towns"].values():
        for who, a in t["agents"].items():
            if not a["health"]:
                continue
            # A developed well halves food needs (same parity for all residents).
            meal = not (t["projects"]["well"]["level"] and t["day"] % 2 == 0)
            if has_effect(t, a, "food_preservation") and t["day"] % 3 == 0:
                meal = False
            used = 1 if meal and a["inventory"]["food"] else 0
            hungry = bool(meal and not used)
            if hungry:
                a["health"] = max(0, a["health"] - 1)
            # Homes/clinic do not erase hunger; the resident must actively rest.
            emit(t, events, "sunset", who,
                 "went hungry" if hungry else "ate supper" if used else "well supplied supper",
                 {who: {"food": -used}}, hungry=hungry, health=a["health"])
        if t["day"] % RAID_EVERY == 0:
            pct = RAID_PCT[t["projects"]["army"]["level"]]
            for who, a in t["agents"].items():
                loss = a["inventory"]["food"] * pct // 100 if a["health"] and not has_effect(t, a, "granary") else 0
                if loss:
                    emit(t, events, "raid", who, f"raiders took {loss} food", {who: {"food": -loss}},
                         amount=loss, army=t["projects"]["army"]["level"])
        expired = [o["id"] for o in t["offers"] if o["expires"] <= t["day"]]
        t["offers"] = [o for o in t["offers"] if o["id"] not in expired]
        if expired:
            emit(t, events, "expired", "town", f"offers expired: {expired}", offer_ids=expired)
        t["day"] += 1
    world["day"] += 1
    return events


def observation(world, town, who):
    t, me = world["towns"][town], world["towns"][town]["agents"][who]
    food = me["inventory"]["food"]
    survival = ("STARVING: you have no food. At sunset you lose 1 health. Get food now (gather food, buy it, ask for it)." if not food
                else f"LOW FOOD: {food} meal(s) left. Secure more food before anything else." if food <= 3
                else f"Food for about {food} days. Health {me['health']}/5.")
    raid_in = (RAID_EVERY - world["day"] % RAID_EVERY) % RAID_EVERY
    return dict(day=world["day"], town=town, weather=weather(world), survival=survival,
                next_raid_in_days=raid_in, message_fee=t["fee"], you=copy.deepcopy(me),
                residents=[dict(name=a["name"], role=a["role"], home=a["home"],
                                alive=a["health"] > 0) for a in t["agents"].values()],
                public_projects=copy.deepcopy(t["projects"]),
                town_inventions=[dict(id=x["id"], name=x["name"], inventor=x["inventor"], effect=x["effect"]) for x in t["techs"].values()],
                offers=copy.deepcopy(t["offers"]), public_events=copy.deepcopy(t["recent"][-12:]))


RULES = """You are one resident of a small town, making your own decisions.
RULE 1, ABOVE EVERYTHING ELSE: STAY ALIVE. A dead resident has no objective, no home and no
future. Your private objective only counts while you are alive. Every day check your food and
health (the "survival" line). If food is 3 or less, getting food comes before your objective.
After staying alive, pursue your private objective. Other residents have their own objectives and limited
information. Your temperament describes you. Choose ONE economic action each day and
optionally ONE message. Never narrate an action instead of selecting it. What others
say may be mistaken; only engine-confirmed transactions transfer resources. Messages
and offers are optional. There is no assigned leader. Maximise your objective over
time, not just this turn; aim to stay alive and make progress beyond the target.

Rules: you start with limited food. At sunset you eat 1 food or lose 1 health.
Zero health means permanent inactivity. rest recovers 1 health only if you hold food,
plus clinic level, capped at 5. gather resource food/wood/stone: 2 units, or 4 for your
specialism (farmer/forester/mason). Food gains farm level, minus 1 in dry weather
(minimum 1). Holding a tool adds 1 to wood/stone gathering; tools are not consumed.
craft consumes 2 wood + 1 stone, yields 1 tool (2 for smith).
home builds the next level (max 3), costing 4*next_level wood + 2*next_level stone.
Home ownership satisfies private housing goals; no production bonus.
contribute project/resource/amount deposits goods. When all requirements are met,
the building gains a level and deposits reset for the next upgrade (max level 3).
Farm costs 12 wood+4 stone per level: +1 food gathering per level.
Well costs 6 wood+12 stone: any level removes food needs on even-numbered days;
levels 2/3 have no additional material benefit. Market costs 10 wood+8 stone;
storehouse 14 wood+6 stone; these are civic landmarks, no automatic bonuses.
Clinic costs 8 wood+10 stone+2 tools: adds level to rest recovery.
Private public-project goals count the total units YOU contributed, not building levels.
Coins are a finite medium of exchange; there is no guaranteed buyer, wage or income.

Your town has a POLICE force and an ARMY, both already at level 1 (max 3). Contributing
to them works like any public project: police costs 6 wood+4 stone+1 tool per level, army
8 wood+6 stone+2 tools per level. Raiders from outside reach the town at the end of every
6th day (see next_raid_in_days) and take a share of every resident's food: 20% at army level 1,
10% at level 2, none at level 3. Police deter theft: action take (target, resource, amount 1..3)
tries to seize goods from a resident. It works with chance 50% at police level 1, 30% at
level 2, 15% at level 3. If it fails you pay a 2 coin fine to the town; if it works there is
a 40%, 60% or 80% chance (police level 1, 2, 3) you are caught, return nothing and pay the
victim 3 coins. Otherwise you keep the goods. take is allowed but you may choose not to use it.

offer: give and want resource bundles (food/wood/stone/tools/coins, positive integer
amounts), target a resident name or all. You must currently hold offered goods.
At most 3 open offers per owner. Offers are public, last 4 days, do not reserve goods.
accept offer_id: atomically exchange your payment for the maker's goods, if both can
still pay. cancel offer_id: your own only. give target/give: unconditional gift.
No theft or forced transfers. Other residents cannot be ordered to act by your text.
Messages have to=all or a resident name, text at most 360 characters. The town's
message_fee is charged in coins after the economic action, only on delivery. No
additional charge for offers. You only see your own private inventory/goal/memory.

TECHNOLOGY. You may invent: action invent (name up to 40 characters, effect) costs 4 wood + 4
stone + 2 tools, and you can make 2 inventions. You choose the name and one effect: seed_selection
(+1 food when you gather food), sharp_tools (+1 wood/stone when you gather them), efficient_forge
(+1 tool when you craft), food_preservation (no meal needed on days divisible by 3), granary
(raiders cannot take your food), lockbox (others cannot take goods from you). The invention helps
you. action teach (target, tech_id) gives another resident the same technology for free; you keep it.
Inventions are public (town_inventions). Nobody can make you teach.

ACTION FORMS (use exactly these field names):
{"kind":"gather","resource":"food"} {"kind":"craft"} {"kind":"home"} {"kind":"rest"}
{"kind":"contribute","project":"farm","resource":"wood","amount":4}
{"kind":"offer","give":{"food":2},"want":{"wood":1},"target":"all"} {"kind":"accept","offer_id":3}
{"kind":"give","target":"Ada","give":{"food":2}} {"kind":"take","target":"Ada","resource":"food","amount":2}
{"kind":"invent","name":"Deep Furrow","effect":"seed_selection"} {"kind":"teach","target":"Ada","tech_id":1}
After every action the engine tells you the result in you.last_result on your next turn. Your
notes (memory) are written BEFORE the engine confirms your action, so if last_result says
REJECTED, your action did not happen: correct your notes and fix the fields.

Return JSON: {"action":{"kind":"gather","resource":"food"},
"message":{"to":"all","text":"optional message"},"memory":"brief private notes for next day"}.
Allowed kinds: gather, craft, home, contribute, offer, accept, cancel, give, rest, take, invent, teach.
Use only fields needed by that action. Omit message if you have nothing to say.
Memory replaces old memory; keep important plans or commitments in under 1000 characters.
"""

BUNDLE_SCHEMA = {"type": "object", "properties": {r: {"type": "integer", "minimum": 1, "maximum": 1000} for r in RESOURCES}, "additionalProperties": False}
def _form(kind, required=(), **fields):
    """One action form: exactly these fields, the required ones mandatory. Stops the model mixing fields between actions."""
    props = {"kind": {"type": "string", "enum": [kind]}}
    props.update(fields)
    return {"type": "object", "required": ["kind", *required], "additionalProperties": False, "properties": props}


_AMOUNT = {"type": "integer", "minimum": 1, "maximum": 1000}
_NAME = {"type": "string"}
ACTION_FORMS = [
    _form("gather", ["resource"], resource={"type": "string", "enum": ["food", "wood", "stone"]}),
    _form("craft"), _form("home"), _form("rest"),
    _form("contribute", ["project", "resource", "amount"], project={"type": "string", "enum": list(PROJECTS)},
          resource={"type": "string", "enum": ["wood", "stone", "tools"]}, amount=_AMOUNT),
    _form("offer", ["give", "want"], give=BUNDLE_SCHEMA, want=BUNDLE_SCHEMA, target=_NAME),
    _form("accept", ["offer_id"], offer_id={"type": "integer", "minimum": 1}),
    _form("cancel", ["offer_id"], offer_id={"type": "integer", "minimum": 1}),
    _form("give", ["target", "give"], target=_NAME, give=BUNDLE_SCHEMA),
    _form("take", ["target", "resource", "amount"], target=_NAME, resource={"type": "string", "enum": list(RESOURCES)},
          amount={"type": "integer", "minimum": 1, "maximum": 3}),
    _form("invent", ["name", "effect"], name={"type": "string", "maxLength": 40}, effect={"type": "string", "enum": list(TECH_EFFECTS)}),
    _form("teach", ["target", "tech_id"], target=_NAME, tech_id={"type": "integer", "minimum": 1}),
]


SCHEMA = {
    "type": "object", "required": ["action", "memory"], "additionalProperties": False,
    "properties": {
        "action": {"anyOf": ACTION_FORMS},
        "message": {"type": "object", "required": ["to", "text"], "additionalProperties": False,
                    "properties": {"to": {"type": "string"}, "text": {"type": "string", "maxLength": 360}}},
        "memory": {"type": "string", "maxLength": 1000},
    },
}
