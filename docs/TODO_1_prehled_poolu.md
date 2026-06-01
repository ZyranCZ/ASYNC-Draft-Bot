# 📝 TODO #1 — Finální podoba přehledu poolu (zpráva po picku)

Cíl: po picku zobrazit zkrácený výpis poolu + souhrn (pitche, equipment sloty,
rozdělení podle slotů, RF řádek) + Fabrary odkaz.

Vše se dělá v souboru **bot.py**. Jsou to 4 zásahy.

---

## Zásah 1 — import re

Nahoře mezi importy ověř, že máš:

    import re

Pokud chybí, přidej ho.

---

## Zásah 2 — konstanty a pomocné funkce

Vlož ZA řádek, kde se načítá MODEL
(`MODEL, ERRORS, WARNINGS = parse_draftmancer(...)`):

```python
EXCLUDED_SLOTS = {"Equipment", "rare", "Mythic", "RFCommon", "RFRare", "RFMythic"}
RF_SLOTS = {"RFCommon", "RFRare", "RFMythic"}


def pitch_of(name):
    m = re.search(r"\((red|yellow|blue)\)", name.lower())
    return m.group(1) if m else None


def short_name(name):
    return name.replace("(red)", "(r)").replace("(yellow)", "(y)").replace("(blue)", "(b)")


def relevant_slots():
    return [s for s in MODEL.get("slotPools", {}) if s not in EXCLUDED_SLOTS]


def pretty_slot(slot):
    return re.sub(r"(?<!^)(?=[A-Z])", " ", slot)


def build_home_slot_map():
    home = {}
    for slot, pool in MODEL["slotPools"].items():
        if slot in EXCLUDED_SLOTS:
            continue
        for e in pool:
            home.setdefault(e["name"], slot)
    return home


HOME_SLOT_MAP = build_home_slot_map()
```

---

## Zásah 3 — nahradit format_pool a přidat pool_summary

Najdi STÁVAJÍCÍ funkci `format_pool` (ta s raritou) a nahraď ji touto dvojicí:

```python
def format_pool(pool):
    if not pool:
        return "_(zatím prázdný)_"
    return "\n".join(
        f"{i}. {short_name(c['name'])}{' [RF]' if c.get('rf') else ''}"
        for i, c in enumerate(pool, 1)
    )


def pool_summary(pool):
    pitch = {"red": 0, "yellow": 0, "blue": 0}
    slots = {"Head": [], "Chest": [], "Arms": [], "Legs": []}
    layout_counts = {s: 0 for s in relevant_slots()}
    rf_rare_mythic = []
    for c in pool:
        p = pitch_of(c["name"])
        if p:
            pitch[p] += 1
        for s in slots:
            if s in (c.get("type") or []):
                slots[s].append(short_name(c["name"]))
        cs = c.get("slot")
        if cs in RF_SLOTS:
            home = HOME_SLOT_MAP.get(c["name"])
            if home in layout_counts:
                layout_counts[home] += 1
            else:
                rf_rare_mythic.append(short_name(c["name"]))
        elif cs in layout_counts:
            layout_counts[cs] += 1

    def slot_line(label, cards):
        return f"**{label}:** " + (", ".join(cards) if cards else "—")

    layout_lines = "\n\n".join(
        f"**{pretty_slot(s)}:** {n}" for s, n in layout_counts.items()
    )
    rf_line = "**Rare / Mythic (RF):** " + (
        ", ".join(rf_rare_mythic) if rf_rare_mythic else "—"
    )
    return (
        "\n---\n**Přehled podle typu karet:**\n\n"
        f"🔴 (red pitch): {pitch['red']}\n\n"
        f"🟡 (yellow pitch): {pitch['yellow']}\n\n"
        f"🔵 (blue pitch): {pitch['blue']}\n\n"
        f"{slot_line('Head', slots['Head'])}\n\n"
        f"{slot_line('Chest', slots['Chest'])}\n\n"
        f"{slot_line('Arms', slots['Arms'])}\n\n"
        f"{slot_line('Legs', slots['Legs'])}\n\n"
        "---\n**Rozdělení podle slotů:**\n\n"
        f"{layout_lines}\n\n{rf_line}"
    )
```

---

## Zásah 4 — upravit skládání zprávy v příkazu pick

V příkazu `pick` najdi část, kde se sestavuje proměnná `zprava`,
a nahraď ji tímto:

```python
    rf = " [RF]" if chosen.get("rf") else ""
    url = build_fabrary_url(seat.pool)
    zprava = (
        f"✅ Vybral sis: **{short_name(chosen['name'])}{rf}**\n\n"
        f"__**Tvůj dosavadní pool ({len(seat.pool)}):**__\n\n"
        f"{format_pool(seat.pool)}\n"
        f"{pool_summary(seat.pool)}\n\n"
        f"📦 [Zobrazit celý balíček na Fabrary]({url})"
    )
    await interaction.response.send_message(zprava)
```

---

## Po dokončení

1. Ulož (Ctrl+S).
2. V terminálu: Ctrl+C, pak `python bot.py`.
3. Otestuj `/pick` — měl by se objevit zkrácený pool + souhrn + odkaz.

## Poznámky

- Funguje napříč sety: sloty se berou z načteného setu, nic není zadrátované
  kromě EXCLUDED_SLOTS / RF_SLOTS (kategorie stejné napříč sety).
- ZNÁMÉ RIZIKO: u plného poolu (~42 karet) s dlouhými názvy + Fabrary URL
  může zpráva přesáhnout limit 2000 znaků a spadnout. Neřeší se teď —
  ošetřit, až to nastane (nejspíš poslat URL jako druhou zprávu).
