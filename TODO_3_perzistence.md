# 📝 TODO #3 — Perzistence (uložení a obnova draftu)

Cíl: rozehraný draft přežije restart bota. Stav se ukládá do
**draft_state.json** po každé změně (atomicky, bezpečně i při souběhu picků)
a při startu bota se obnoví.

⚠️ ZÁVISLOST: nejdřív musí být hotové **TODO #2** (balíček jako objekt Pack).
Perzistence ukládá Pack objekty — bez TODO #2 nebude fungovat.

Vše v souboru **bot.py**.

---

## Zásah 1 — importy

Nahoře mezi importy přidej (pokud chybí):

```python
import json
import os
import asyncio
```

---

## Zásah 2 — serializace v třídě Pack

Do třídy `Pack` (z TODO #2) přidej dvě metody:

```python
    def to_dict(self):
        return {
            "cards": self.cards,
            "origin_seat": self.origin_seat,
            "pack_number": self.pack_number,
        }

    @staticmethod
    def from_dict(d):
        return Pack(d["cards"], d["origin_seat"], d["pack_number"])
```

---

## Zásah 3 — serializace v třídě Draft

Do třídy `Draft` přidej tyto metody (klidně na konec třídy):

```python
    def to_dict(self):
        return {
            "current_pack_number": self.current_pack_number,
            "running": self.running,
            "seats": [{
                "number": st.number,
                "player_id": st.player_id,
                "pool": st.pool,
                "active_pack": st.active_pack.to_dict() if st.active_pack else None,
                "queue": [p.to_dict() for p in st.queue],
            } for st in self.seats],
        }

    def load_dict(self, d):
        self.current_pack_number = d["current_pack_number"]
        self.running = d["running"]
        for st, sd in zip(self.seats, d["seats"]):
            st.player_id = sd["player_id"]
            st.pool = sd["pool"]
            st.active_pack = Pack.from_dict(sd["active_pack"]) if sd["active_pack"] else None
            st.queue = deque(Pack.from_dict(p) for p in sd["queue"])
```

---

## Zásah 4 — ukládací/načítací funkce

Vlož mezi pomocné funkce (kdekoliv po definici DRAFT = Draft(MODEL)):

```python
STATE_FILE = "draft_state.json"
_save_lock = asyncio.Lock()


async def save_state():
    """Atomický zápis stavu draftu. Bezpečné i při souběhu picků."""
    async with _save_lock:
        tmp = STATE_FILE + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(DRAFT.to_dict(), f, ensure_ascii=False)
            os.replace(tmp, STATE_FILE)   # atomické přejmenování
        except Exception as e:
            print("Chyba při ukládání stavu:", e)


def load_state():
    """Načte stav ze souboru, pokud existuje. Volá se při startu."""
    if not os.path.exists(STATE_FILE):
        print("Žádný uložený draft (čistý start).")
        return
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            DRAFT.load_dict(json.load(f))
        print("Stav draftu obnoven ze souboru.")
    except Exception as e:
        print("Chyba při načítání stavu:", e)
```

---

## Zásah 5 — načíst stav při startu

V metodě `on_ready` (nebo setup_hook) zavolej `load_state()`.
Nejlépe v on_ready, až po spárování seat kanálů. Přidej řádek:

```python
    load_state()
```

(klidně hned za výpis "Bot je online...").

---

## Zásah 6 — ukládat po každé změně stavu

Přidej `await save_state()` na konec KAŽDÉ akce, která mění draft.
Konkrétně do těchto slash příkazů, vždy po provedení změny:

### V příkazu `pick` — po odeslání potvrzovací zprávy:
```python
    await save_state()
```
(dej to na konec funkce, za poslání zprávy a za odeslání nových balíčků)

### V příkazu `draft_start` — po open_pack a rozeslání:
```python
    await save_state()
```

### V příkazu `draft_next` — po open_pack a rozeslání:
```python
    await save_state()
```

### V přihlašovacím panelu (JoinPanel), v metodách join i leave —
po nastavení/zrušení seat.player_id:
```python
    await save_state()
```

### V draft_clear (po potvrzení) — pokud maže i stav, ulož po úklidu.
(Pozn.: pokud chceš, aby draft_clear i resetoval draft, řekni — doděláme zvlášť.)

---

## Po dokončení

1. Ulož (Ctrl+S).
2. Ctrl+C, `python bot.py` → mělo by napsat "Žádný uložený draft (čistý start)".
3. Spusť draft, pickni pár karet.
4. Ctrl+C (vypni bota), pak `python bot.py` znovu.
5. Mělo by napsat "Stav draftu obnoven ze souboru." a draft pokračuje
   přesně tam, kde jsi přestal (pooly, balíčky, fronty, přiřazení).

## Poznámky

- Soubor draft_state.json se tvoří ve složce bota. Můžeš si ho otevřít
  a podívat se, co v něm je (je to čitelný JSON).
- Atomický zápis (přes .tmp + přejmenování) + zámek = bezpečné i když
  pickne víc lidí ve stejnou chvíli. Soubor je vždy celý starý nebo celý nový.
- Po dokončení tohoto TODO je odblokovaný dropdown picker (ten potřeboval
  perzistenci, aby fungoval i po restartu).
- Pozn. k panelu: po restartu se obnoví i to, jestli draft běží (running),
  takže zamčení přihlašovacího panelu po startu bude konzistentní.
