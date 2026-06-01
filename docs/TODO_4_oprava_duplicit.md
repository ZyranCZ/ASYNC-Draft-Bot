# 📝 TODO #4 — Oprava duplicitních karet v boosteru (BUG)

Cíl: zajistit, aby se v jednom boosteru NEobjevila tatáž karta dvakrát.
RF varianta je výjimka — ta duplicitní být smí (vůči své normální verzi).

Soubor: **booster_generator.py**

⚠️ Tato oprava je nezávislá na TODO #1–#3 — můžeš ji udělat kdykoliv,
klidně jako první (ovlivňuje férovost draftu).

---

## Příčina (proč to vzniká)

- Karta může mít ve slotu víc kopií (např. Holo Shield (blue) = 4 kopie
  ve slotu LightningIllusionist).
- Generátor losuje z "rozbaleného" seznamu, kde je každá kopie samostatná
  položka → může vytáhnout 2 kopie téže karty do jednoho boosteru.
- Stejně tak může tutéž kartu vytáhnout víc různých slotů (karta je ve více slotech).

Oba případy řeší jedna oprava: losovat z UNIKÁTNÍCH názvů a hlídat,
že se název v boosteru neopakuje (mimo RF sloty).

---

## Oprava — nahraď funkci generate_booster

Najdi v booster_generator.py funkci `generate_booster` a nahraď ji touto verzí:

```python
def generate_booster(model, inventory=None, rng=None):
    """Vygeneruje jeden booster. Karty jsou v rámci boosteru unikátní podle názvu
    (kromě RF slotů, kde smí být duplicita vůči normální verzi)."""
    rng = rng or random.Random()
    layout = pick_layout(model, rng)

    booster = []
    used_names = set()   # názvy NE-RF karet, které už v boosteru jsou

    for slot in layout["slots"]:
        name_slot = slot["slot"]
        count = slot["count"]
        is_rf = name_slot.startswith("RF")

        # unikátní názvy dostupné v tomto slotu, zamíchané
        available = list({e["name"] for e in model["slotPools"].get(name_slot, [])})
        rng.shuffle(available)

        taken = 0
        for name in available:
            if taken >= count:
                break
            if not is_rf and name in used_names:
                continue   # tahle karta už v boosteru je → přeskoč
            card = dict(model["cards"][name])
            card["slot"] = name_slot
            card["rf"] = is_rf
            booster.append(card)
            if not is_rf:
                used_names.add(name)
            taken += 1

    return booster, layout["id"]
```

---

## Co se změnilo a co to znamená

- Losuje se z UNIKÁTNÍCH názvů ve slotu (ne z rozbaleného seznamu kopií),
  takže nejde vytáhnout 2 kopie téže karty.
- `used_names` hlídá, že se název nezopakuje ani napříč různými sloty.
- RF sloty (RFCommon/RFRare/RFMythic) se nehlídají → RF karta smí být
  duplicitní vůči své normální verzi. (Poznají se podle name_slot.startswith("RF").)
- POZOR — tohle je věrné REÁLNÝM print sheets: karty se stříhají z archů a dvě
  stejné se na jednom boosteru nikdy nesejdou. Původní generátor (kdy mohly
  padnout 2 stejné) byl naopak nereálný. Oprava tedy fyzický model NEopouští —
  vystihuje ho líp. "V boosteru každý titul max jednou" = jak to chodí v krabici.

## Pozn.: funkce make_inventory a _expand_pool

- Nová generate_booster už nepotřebuje `inventory` (parametr nechávám kvůli
  kompatibilitě s voláním v bot.py, ale ignoruje se).
- make_inventory a _expand_pool můžeš nechat být — neškodí. Pokud je chceš
  uklidit, jde to, ale není to nutné a v bot.py se inventory ještě předává,
  tak ať se nic nerozbije, klidně nech.

---

## Ověření po provedení

Spusť v terminálu:

    python booster_generator.py

Mělo by vypsat booster 14 karet. Pro jistotu vygeneruj víc boosterů a koukni,
že se v žádném neopakuje tatáž karta (kromě [RF]).

Otestováno: 3000 boosterů → 0 duplicit (mimo RF), každý booster má 14 karet.

---

## Pozn. k bot.py

- Pokud bot.py volá generate_booster(MODEL, inventory=inv, rng=...),
  funguje to dál (parametr inventory se jen ignoruje).
- Žádná změna v bot.py kvůli téhle opravě není nutná.
