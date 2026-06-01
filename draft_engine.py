"""
Motor asynchronního draftu (jádro, bez Discordu).

Pravidla:
- 8 seatů v kruhu.
- Každý pack koluje mezi seaty; hráč si vezme 1 kartu, zbytek pošle dál.
- Každý seat má max 1 AKTIVNÍ pack. Další příchozí packy čekají ve FRONTĚ.
- Směr předávání se střídá podle čísla packu: forward, backward, forward.
- Pack je hotový, když v něm nezbývá karta. Kolo končí, když jsou hotové všechny.
"""

import random
from collections import deque


class Seat:
    def __init__(self, number):
        self.number = number
        self.active_pack = None       # seznam karet, nebo None
        self.queue = deque()          # čekající packy
        self.pool = []                # nabrané karty

    def has_active(self):
        return self.active_pack is not None


class Draft:
    def __init__(self, model, num_seats=8, num_packs=3):
        self.model = model
        self.num_seats = num_seats
        self.num_packs = num_packs
        self.seats = [Seat(i + 1) for i in range(num_seats)]
        self.directions = ["forward", "backward", "forward"]
        self.current_pack_number = 0   # 0 = ještě nezačalo
        self.inventory = None

    # --- směr a sousedé ---
    def direction(self):
        return self.directions[self.current_pack_number - 1]

    def next_seat_index(self, idx):
        """Index seatu, kam se pošle pack, podle aktuálního směru."""
        if self.direction() == "forward":
            return (idx + 1) % self.num_seats
        else:
            return (idx - 1) % self.num_seats

    # --- otevření nového kola ---
    def open_pack(self, pack_number):
        from booster_generator import generate_booster, make_inventory
        self.current_pack_number = pack_number
        # nový inventář kopií pro každé kolo
        self.inventory = make_inventory(self.model)
        for seat in self.seats:
            booster, _ = generate_booster(self.model, inventory=self.inventory)
            seat.active_pack = booster

    # --- pick ---
    def pick(self, seat_index, card_index):
        seat = self.seats[seat_index]
        if not seat.has_active():
            raise ValueError(f"Seat {seat.number} nemá aktivní pack.")
        pack = seat.active_pack
        if card_index < 0 or card_index >= len(pack):
            raise ValueError("Neplatné číslo karty.")

        # 1) přesuň kartu do poolu
        chosen = pack.pop(card_index)
        seat.pool.append(chosen)

        # 2) zbytek packu pošli dál (pokud něco zbylo)
        if pack:
            tgt = self.seats[self.next_seat_index(seat_index)]
            if tgt.has_active():
                tgt.queue.append(pack)        # cíl má aktivní → do fronty
            else:
                tgt.active_pack = pack         # cíl je volný → rovnou aktivní

        # 3) tomuto seatu nastav další pack z fronty (nebo nic)
        seat.active_pack = seat.queue.popleft() if seat.queue else None

    # --- je kolo hotové? ---
    def round_finished(self):
        for seat in self.seats:
            if seat.has_active() or seat.queue:
                return False
        return True


def simulate():
    from draftmancer_parser import parse_draftmancer
    model, errors, _ = parse_draftmancer("OMN_Draft_3_5.txt", "omn")
    if errors:
        print("Chyba načtení setu:", errors)
        return

    rng = random.Random(7)
    draft = Draft(model, num_seats=8, num_packs=3)

    for pack_no in range(1, draft.num_packs + 1):
        draft.open_pack(pack_no)
        print(f"\n=== Pack {pack_no} otevřen (směr {draft.direction()}) ===")

        picks = 0
        # dokud kolo neskončí, hledej seaty s aktivním packem a pickej
        while not draft.round_finished():
            progressed = False
            for idx, seat in enumerate(draft.seats):
                if seat.has_active():
                    n = len(seat.active_pack)
                    draft.pick(idx, rng.randrange(n))   # náhodný pick
                    picks += 1
                    progressed = True
            if not progressed:
                print("  ! Uváznutí — nikdo nemá aktivní pack, ale kolo není hotové.")
                break
        print(f"  Picků v tomto kole: {picks}")

    # kontrola výsledku
    print("\n=== Výsledek ===")
    total = 0
    for seat in draft.seats:
        print(f"Seat {seat.number}: {len(seat.pool)} karet")
        total += len(seat.pool)
    print(f"Celkem nabraných karet: {total}")
    print(f"Očekáváno: 8 seatů × 3 packy × 14 karet = {8*3*14}")


if __name__ == "__main__":
    simulate()
