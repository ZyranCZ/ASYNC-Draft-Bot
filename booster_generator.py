"""Generátor boosteru: vážený výběr layoutu + tahání ze slotů."""

import random
from draftmancer_parser import parse_draftmancer
import re

def base_name(name):
    """Název karty bez pitch koncovky: 'Ebbing Arcstride (red)' -> 'Ebbing Arcstride'."""
    return re.sub(r"\s*\((red|yellow|blue)\)\s*$", "", name, flags=re.I).strip()

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
    """Vygeneruje jeden booster. Karty jsou v rámci boosteru unikátní podle
    ZÁKLADNÍHO názvu (bez pitche) — žádné dvě pitch varianty téže karty.
    Výjimka: RF sloty se nehlídají (RF varianta smí být duplicitní)."""
    rng = rng or random.Random()
    layout = pick_layout(model, rng)

    booster = []
    used_bases = set()   # base názvy NE-RF karet, které už v boosteru jsou

    for slot in layout["slots"]:
        name_slot = slot["slot"]
        count = slot["count"]
        is_rf = name_slot.startswith("RF")

        # unikátní celé názvy dostupné v tomto slotu, zamíchané
        available = list({e["name"] for e in model["slotPools"].get(name_slot, [])})
        rng.shuffle(available)

        taken = 0
        for name in available:
            if taken >= count:
                break
            b = base_name(name)
            if not is_rf and b in used_bases:
                continue   # tato karta (i v jiné barvě) už v boosteru je → přeskoč
            card = dict(model["cards"][name])
            card["slot"] = name_slot
            card["rf"] = is_rf
            booster.append(card)
            if not is_rf:
                used_bases.add(b)
            taken += 1

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