# 📝 TODO #2 — Balíček s identitou + nový nadpis

Cíl: nadpis balíčku ve formátu **`Seat 4's Pack #1 — Pick #4`**
(původní seat balíčku + kolikátý pack + kolikátá karta se zrovna bere).

K tomu balíček přestává být jen seznam karet a stává se objektem `Pack`,
který nese: karty, origin_seat, pack_number.

⚠️ Toto je provázaná změna napříč motorem. Měň CELÉ bloky, ne útržky,
ať někde nezůstane starý `len(pack)` místo `len(pack.cards)`.

Vše v souboru **bot.py**.

---

## Zásah 1 — přidat třídu Pack

Vlož NAD třídu `Seat` (klidně hned za konstanty NUM_SEATS / DIRECTIONS):

```python
PACK_SIZE = 14


class Pack:
    def __init__(self, cards, origin_seat, pack_number):
        self.cards = cards
        self.origin_seat = origin_seat
        self.pack_number = pack_number

    def pick_number(self):
        # kolikátá karta se z balíčku zrovna bere (1..PACK_SIZE)
        return PACK_SIZE - len(self.cards) + 1

    def title(self):
        return f"Seat {self.origin_seat}'s Pack #{self.pack_number} — Pick #{self.pick_number()}"
```

---

## Zásah 2 — nahradit metodu open_pack v třídě Draft

Najdi STÁVAJÍCÍ `def open_pack` a nahraď ji touto verzí
(vytváří Pack objekty místo holých seznamů):

```python
    def open_pack(self, pack_number):
        self.current_pack_number = pack_number
        self.inventory = make_inventory(self.model)
        for seat in self.seats:
            cards, _ = generate_booster(self.model, inventory=self.inventory)
            seat.active_pack = Pack(cards, origin_seat=seat.number,
                                    pack_number=pack_number)
            seat.queue.clear()
```

---

## Zásah 3 — nahradit metodu pick v třídě Draft

Najdi STÁVAJÍCÍ `def pick(self, seat_index, card_index)` (metoda v třídě Draft,
NE slash příkaz) a nahraď ji touto verzí (pracuje s pack.cards):

```python
    def pick(self, seat_index, card_index):
        seat = self.seats[seat_index]
        pack = seat.active_pack
        chosen = pack.cards.pop(card_index)
        seat.pool.append(chosen)

        newly_active = []

        # zbytek balíčku pošli dál (pokud něco zbylo)
        if pack.cards:
            tgt = self.seats[self.next_seat_index(seat_index)]
            if tgt.has_active():
                tgt.queue.append(pack)
            else:
                tgt.active_pack = pack
                newly_active.append(tgt)

        # tomuto seatu vytáhni další z fronty
        if seat.queue:
            seat.active_pack = seat.queue.popleft()
            newly_active.append(seat)
        else:
            seat.active_pack = None

        return chosen, newly_active
```

Pozn.: `has_active()` v třídě Seat zůstává beze změny — pořád testuje
`self.active_pack is not None`, což pro Pack objekt funguje stejně.

---

## Zásah 4 — nahradit build_pack_view

Najdi STÁVAJÍCÍ `def build_pack_view(...)` a nahraď ji touto verzí.
Bere teď Pack objekt (ne seznam) a do nadpisu dá pack.title():

```python
def build_pack_view(pack):
    view = ui.LayoutView()
    container = ui.Container()
    for pair in chunk_pairs(pack.cards):
        gallery = ui.MediaGallery()
        for card in pair:
            gallery.add_item(media=card["imageUrl"])
        container.add_item(gallery)
    container.add_item(ui.Separator())
    lines = [f"__**{pack.title()} — vyber kartu pomocí /pick [číslo]:**__"]
    for i, c in enumerate(pack.cards, 1):
        rf = " [RF]" if c.get("rf") else ""
        lines.append(f"{i}) {short_name(c['name'])}{rf}")
    container.add_item(ui.TextDisplay("\n".join(lines)))
    view.add_item(container)
    return view
```

(Pozn.: použil jsem i short_name pro zkrácení pitchů v seznamu balíčku —
sjednoceno s přehledem poolu. Vyžaduje, abys měl hotové TODO #1, kde se
short_name přidává. Pokud TODO #1 ještě nemáš, nahraď short_name(c['name'])
zpět za c['name'].)

---

## Zásah 5 — upravit send_pack_to_seat

Najdi `async def send_pack_to_seat(seat)` a uprav volání build_pack_view
tak, aby předávalo celý Pack objekt (ne active_pack jako seznam).
Nová verze:

```python
async def send_pack_to_seat(seat):
    if not seat.has_active() or seat.channel_id is None:
        return
    channel = client.get_channel(seat.channel_id)
    if channel:
        view = build_pack_view(seat.active_pack)
        await channel.send(view=view)
```

---

## Zásah 6 — upravit validaci v slash příkazu pick

Ve slash příkazu `async def pick(interaction, cislo)` se na dvou místech
sahá na balíček jako na seznam. Najdi řádky, kde se testuje délka, např.:

```python
    if cislo < 1 or cislo > len(seat.active_pack):
        await interaction.response.send_message(
            f"Neplatná volba. Vyber číslo od 1 do {len(seat.active_pack)}.", ephemeral=True)
        return
```

a nahraď `len(seat.active_pack)` za `len(seat.active_pack.cards)` (na obou místech):

```python
    if cislo < 1 or cislo > len(seat.active_pack.cards):
        await interaction.response.send_message(
            f"Neplatná volba. Vyber číslo od 1 do {len(seat.active_pack.cards)}.", ephemeral=True)
        return
```

---

## Kontrola — kde všude se sahá na balíček

Projdi bot.py a najdi (Ctrl+F) všechny výskyty `active_pack`.
Kdekoliv se s ním zacházelo jako se SEZNAMEM karet (len(...), indexace [...],
iterace přes karty), musí být teď `.cards`:
- `len(seat.active_pack)`         → `len(seat.active_pack.cards)`
- `seat.active_pack[i]`           → `seat.active_pack.cards[i]`
- `for c in seat.active_pack`     → `for c in seat.active_pack.cards`

Naopak `has_active()` a `seat.active_pack = ...` / `= None` zůstávají.

---

## Po dokončení

1. Ulož (Ctrl+S).
2. Ctrl+C, `python bot.py`.
3. `/draft_start`, pak `/pick` — nadpis balíčku by měl ukazovat
   `Seat X's Pack #Y — Pick #Z`.
4. Pickni vícekrát a sleduj, že Pick # roste a origin Seat zůstává.

## Poznámka

- Tato změna („balíček s identitou") se bude hodit i pro budoucí nápady:
  log picků, práskač AFK, přehled stavu — všechny chtějí vědět, který
  balíček je který.
