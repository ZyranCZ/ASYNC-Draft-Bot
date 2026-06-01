"""Generátor boosteru: vážený výběr layoutu + tahání ze slotů."""

import random
from draftmancer_parser import parse_draftmancer


def _expand_pool(pool):
    flat = []
    for entry in pool:
        flat.extend([entry["name"]] * entry["copies"])
    return flat


def make_inventory(model):
    return {slot: _expand_pool(pool) for slot, pool in model["slotPools"].items()}


def pick_layout(model, rng):
    layouts = model["layouts"]
    weights = [L["weight"] for L in layouts]
    return rng.choices(layouts, weights=weights, k=1)[0]


def generate_booster(model, inventory=None, rng=None):
    rng = rng or random.Random()
    with_replacement = model["settings"].get("withReplacement", False)
    layout = pick_layout(model, rng)

    booster = []
    for slot in layout["slots"]:
        name_slot = slot["slot"]
        count = slot["count"]
        if with_replacement:
            names = [e["name"] for e in model["slotPools"].get(name_slot, [])]
            chosen = [rng.choice(names) for _ in range(count)] if names else []
        else:
            bag = inventory[name_slot]
            take = min(count, len(bag))
            chosen = rng.sample(bag, take)
            for c in chosen:
                bag.remove(c)
        for name in chosen:
            card = dict(model["cards"][name])
            card["slot"] = name_slot
            card["rf"] = name_slot.startswith("RF")
            booster.append(card)
    return booster, layout["id"]


if __name__ == "__main__":
    model, errors, warnings = parse_draftmancer("OMN_Draft_3_5.txt", "omn")
    rng = random.Random(42)
    inv = make_inventory(model)
    booster, layout_id = generate_booster(model, inventory=inv, rng=rng)
    print(f"Layout: {layout_id}, karet: {len(booster)}\n")
    for i, c in enumerate(booster, 1):
        rf = " [RF]" if c.get("rf") else ""
        print(f"{i:>2}. {c['name']}{rf}  ({c['slot']}, {c['rarity']})")