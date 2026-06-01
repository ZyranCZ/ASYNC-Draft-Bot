"""Parser Draftmancer .txt souboru do interního modelu, s validací."""

import json
import re

SECTION_HEADER = re.compile(r"^\[([A-Za-z0-9_]+)\]\s*$")
LAYOUT_LINE = re.compile(r"^\s*-\s*(\S+)\s*\((\d+)\)\s*$")
COUNT_LINE = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")


def _split_sections(text):
    sections = {}
    current_name = None
    current_lines = []
    for line in text.splitlines():
        m = SECTION_HEADER.match(line)
        if m:
            if current_name is not None:
                sections[current_name] = current_lines
            current_name = m.group(1)
            current_lines = []
        else:
            if current_name is not None:
                current_lines.append(line)
    if current_name is not None:
        sections[current_name] = current_lines
    return sections


def _parse_layouts(lines, errors):
    layouts = []
    current = None
    for line in lines:
        if not line.strip():
            continue
        m_layout = LAYOUT_LINE.match(line)
        if m_layout:
            current = {"id": m_layout.group(1), "weight": int(m_layout.group(2)), "slots": []}
            layouts.append(current)
            continue
        m_slot = COUNT_LINE.match(line)
        if m_slot:
            if current is None:
                errors.append(f"Slot '{line.strip()}' se objevil před prvním layoutem.")
                continue
            current["slots"].append({"slot": m_slot.group(2).strip(), "count": int(m_slot.group(1))})
            continue
        errors.append(f"Nerozpoznaný řádek v [Layouts]: {line.strip()!r}")
    return layouts


def _parse_slot_pool(name, lines, errors):
    pool = []
    for line in lines:
        if not line.strip():
            continue
        m = COUNT_LINE.match(line)
        if not m:
            errors.append(f"Řádek v slotu [{name}] nezačíná počtem kopií: {line.strip()!r}")
            continue
        pool.append({"name": m.group(2).strip(), "copies": int(m.group(1))})
    return pool


def parse_draftmancer(path, set_id="set"):
    errors = []
    warnings = []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    sections = _split_sections(text)

    for required in ("Settings", "CustomCards", "Layouts"):
        if required not in sections:
            errors.append(f"Chybí povinná sekce [{required}].")
    if errors:
        return None, errors, warnings

    settings = {}
    try:
        settings = json.loads("\n".join(sections["Settings"]))
        if not isinstance(settings, dict):
            errors.append("[Settings] není JSON objekt.")
    except json.JSONDecodeError as e:
        errors.append(f"[Settings] není validní JSON: {e}")

    cards = {}
    try:
        raw_cards = json.loads("\n".join(sections["CustomCards"]))
        if not isinstance(raw_cards, list):
            errors.append("[CustomCards] není JSON pole.")
            raw_cards = []
    except json.JSONDecodeError as e:
        errors.append(f"[CustomCards] není validní JSON: {e}")
        raw_cards = []

    for card in raw_cards:
        if "name" not in card or "rarity" not in card:
            errors.append(f"Karta postrádá name nebo rarity: {card!r}")
            continue
        type_raw = card.get("type", "")
        cards[card["name"]] = {
            "name": card["name"],
            "rarity": card["rarity"],
            "collectorNumber": card.get("collector_number"),
            "manaCost": card.get("mana_cost"),
            "type": [t.strip() for t in type_raw.split(",")] if type_raw else [],
            "imageUrl": (card.get("image_uris") or {}).get("en"),
        }

    layouts = _parse_layouts(sections["Layouts"], errors)
    for layout in layouts:
        if not layout["slots"]:
            errors.append(f"Layout {layout['id']} nemá žádný slot.")

    known = {"Settings", "CustomCards", "Layouts"}
    slot_pools = {}
    for name, lines in sections.items():
        if name in known:
            continue
        slot_pools[name] = _parse_slot_pool(name, lines, errors)

    for layout in layouts:
        for s in layout["slots"]:
            if s["slot"] not in slot_pools:
                errors.append(f"Layout {layout['id']} odkazuje na slot [{s['slot']}], ale ta v souboru neexistuje.")

    for name, pool in slot_pools.items():
        for entry in pool:
            if entry["name"] not in cards:
                warnings.append(f'Karta "{entry["name"]}" je ve slotu [{name}], ale není v [CustomCards].')

    model = {
        "setId": set_id,
        "sourceFormat": "draftmancer-txt",
        "settings": {
            "showSlots": settings.get("showSlots", False),
            "withReplacement": settings.get("withReplacement", False),
            "cardBack": settings.get("cardBack"),
        },
        "cards": cards,
        "layouts": layouts,
        "slotPools": slot_pools,
    }
    return model, errors, warnings


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "OMN_Draft_3_5.txt"
    model, errors, warnings = parse_draftmancer(path, set_id="omn")
    if errors:
        print("Import selhal:")
        for e in errors:
            print("  CHYBA:", e)
    else:
        print(f"Set importován: {model['setId']}")
        print(f"Karet: {len(model['cards'])}, Layoutů: {len(model['layouts'])}, Slot-poolů: {len(model['slotPools'])}")
        print(f"withReplacement: {model['settings']['withReplacement']}")
        for w in warnings:
            print("  VAROVÁNÍ:", w)