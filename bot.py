import os
import random
import discord
import re
from discord import app_commands, ui
from dotenv import load_dotenv
from collections import deque
from urllib.parse import quote
from datetime import date

from draftmancer_parser import parse_draftmancer
from booster_generator import generate_booster, make_inventory

load_dotenv()

MODEL, ERRORS, WARNINGS = parse_draftmancer("OMN_Draft_3_5.txt", "omn")
if ERRORS:
    print("POZOR, set se nenačetl správně:", ERRORS)

NUM_SEATS = 8
NUM_PACKS = 3
DIRECTIONS = ["forward", "backward", "forward"]
PACK_SIZE = 14


intents = discord.Intents.default()
intents.message_content = True
intents.members = True



# ---------- MOTOR DRAFTU ----------
class Seat:
    def __init__(self, number):
        self.number = number
        self.channel_id = None
        self.player_id = None
        self.active_pack = None
        self.queue = deque()
        self.pool = []

    def has_active(self):
        return self.active_pack is not None


class Draft:
    def __init__(self, model):
        self.model = model
        self.seats = [Seat(i + 1) for i in range(NUM_SEATS)]
        self.current_pack_number = 0
        self.inventory = None
        self.running = False

    def seat_by_channel(self, channel_id):
        for s in self.seats:
            if s.channel_id == channel_id:
                return s
        return None

    def direction(self):
        return DIRECTIONS[self.current_pack_number - 1]

    def next_seat_index(self, idx):
        if self.direction() == "forward":
            return (idx + 1) % NUM_SEATS
        return (idx - 1) % NUM_SEATS

    def open_pack(self, pack_number):
        self.current_pack_number = pack_number
        self.inventory = make_inventory(self.model)
        for seat in self.seats:
            cards, _ = generate_booster(self.model, inventory=self.inventory)
            seat.active_pack = Pack(cards, origin_seat=seat.number,
                                    pack_number=pack_number)
            seat.queue.clear()

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

    def round_finished(self):
        return all(not s.has_active() and not s.queue for s in self.seats)

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

DRAFT = Draft(MODEL)


# ---------- DISCORD KLIENT ----------
class DraftBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(JoinPanel())
        guild = discord.Object(id=1048530000963440710)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        print(f"Zaregistrováno příkazů na server: {len(synced)}")
        for c in synced:
            print("  -", c.name)


client = DraftBot()


ADMIN_CHANNEL_ID = None   # sem se uloží ID kanálu draft-pod-1


@client.event
async def on_ready():
    global ADMIN_CHANNEL_ID
    found = 0
    for guild in client.guilds:
        for channel in guild.text_channels:
            for i in range(1, NUM_SEATS + 1):
                if channel.name == f"seat-{i}":
                    DRAFT.seats[i - 1].channel_id = channel.id
                    found += 1
            if channel.name == "draft-pod-1":
                ADMIN_CHANNEL_ID = channel.id
    admin_ok = "ano" if ADMIN_CHANNEL_ID else "NENALEZEN"
    print(f"Bot je online jako {client.user}! Seat kanálů: {found}/{NUM_SEATS}, draft-pod-1: {admin_ok}")



# ---------- POMOCNÉ ----------
def chunk_pairs(seq):
    return [seq[i:i + 2] for i in range(0, len(seq), 2)]


def build_pack_view(pack):
    view = ui.LayoutView()
    container = ui.Container()
    for pair in chunk_pairs(pack.cards):
        gallery = ui.MediaGallery()
        for card in pair:
            gallery.add_item(media=card["imageUrl"])
        container.add_item(gallery)
    container.add_item(ui.Separator())
    lines = [f"**{pack.title()}\nVyber kartu pomocí /pick [číslo]:**\n"]
    for i, c in enumerate(pack.cards, 1):
        rf = " [RF]" if c.get("rf") else ""
        lines.append(f"{i}) {short_name(c['name'])}{rf}")
    container.add_item(ui.TextDisplay("\n".join(lines)))
    view.add_item(container)
    return view

def pitch_of(name):
    m = re.search(r"\((red|yellow|blue)\)", name.lower())
    return m.group(1) if m else None

def short_name(name):
    return (name
            .replace("(red)", "(R)")
            .replace("(yellow)", "(Y)")
            .replace("(blue)", "(B)"))

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
    for c in pool:
        p = pitch_of(c["name"])
        if p:
            pitch[p] += 1
        for s in slots:
            if s in (c.get("type") or []):
                slots[s].append(short_name(c["name"]))

    def slot_line(label, cards):
        return f"**{label}:** " + (", ".join(cards) if cards else "—")

    return (
        "\n\n**—————PITCH—————**\n"
        f"🔴{pitch['red']}     🟡{pitch['yellow']}     🔵{pitch['blue']}\n"
        f"{slot_line('HEAD', slots['Head'])}\n"
        f"{slot_line('CHEST', slots['Chest'])}\n"
        f"{slot_line('ARMS', slots['Arms'])}\n"
        f"{slot_line('LEGS', slots['Legs'])}"
    )


TOTAL_PICKS = 42   # 3 packy × 14 karet


def build_fabrary_url(pool, player_name=None):
    base = "https://fabrary.net/decks?tab=import&format=draft"
    parts = [f"&cards={c['collectorNumber']}" for c in pool if c.get("collectorNumber")]
    url = base + "".join(parts)
    if player_name:
        today = date.today().strftime("%d/%m/%Y")
        pick_no = len(pool)   # počet karet v poolu = číslo aktuálního picku
        deck_name = f"{player_name}'s ASYNC Draft {today} (Pick {pick_no:02d}/{TOTAL_PICKS})"
        url += "&name=" + quote(deck_name, safe="")
    return url


async def send_pack_to_seat(seat):
    if not seat.has_active() or seat.channel_id is None:
        return
    channel = client.get_channel(seat.channel_id)
    if channel:
        view = build_pack_view(seat.active_pack)
        await channel.send(view=view)

ORGANIZER_ROLE = "Organizer"
def is_organizer(interaction: discord.Interaction) -> bool:
    """True, pokud má uživatel roli Organizer."""
    if interaction.guild is None:
        return False
    member = interaction.user
    return any(role.name == ORGANIZER_ROLE for role in getattr(member, "roles", []))

# ---------- PŘÍKAZY ----------
@client.tree.command(name="ping", description="Ověří, že bot žije")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓")

# ---------- /draft_clear s potvrzením ----------
class ClearConfirm(ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=30)   # tlačítka platí 30 s
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # tlačítka smí zmáčknout jen ten, kdo příkaz vyvolal
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Tohle tlačítko není pro tebe.", ephemeral=True)
            return False
        return True

    @ui.button(label="Potvrdit smazání", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="🧹 Mažu zprávy v seat kanálech…", view=None)
        report = []
        for seat in DRAFT.seats:
            if seat.channel_id is None:
                continue
            channel = client.get_channel(seat.channel_id)
            if channel is None:
                continue
            try:
                deleted = await channel.purge(limit=1000)   # maže zprávy < 14 dní
                report.append(f"seat-{seat.number}: {len(deleted)}")
            except discord.Forbidden:
                report.append(f"seat-{seat.number}: chybí právo Manage Messages")
            except Exception as e:
                report.append(f"seat-{seat.number}: chyba ({type(e).__name__})")
        await interaction.followup.send("Hotovo. Smazáno:\n" + "\n".join(report), ephemeral=True)

    @ui.button(label="Zrušit", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="Zrušeno, nic se nesmazalo.", view=None)


@client.tree.command(name="draft_clear", description="ADMIN: smaže zprávy ve všech seat kanálech (s potvrzením)")
async def draft_clear(interaction: discord.Interaction):
    if not is_organizer(interaction):
        await interaction.response.send_message(
            "Tohle můžou spustit jen organizátoři (role Organizer).", ephemeral=True)
        return
    await interaction.response.send_message(
        "⚠️ **Tohle nevratně smaže všechny zprávy mladší 14 dní ve všech 8 seat kanálech.**\n"
        "Opravdu pokračovat?",
        view=ClearConfirm(interaction.user.id),
        ephemeral=True,
    )

@client.tree.command(name="draft_start", description="ADMIN: spustí draft a otevře 1. pack")
async def draft_start(interaction: discord.Interaction):
    if not is_organizer(interaction):
        await interaction.response.send_message(
            "Tohle můžou spustit jen organizátoři (role Organizer).", ephemeral=True)
        return
    for s in DRAFT.seats:
        s.pool = []
        s.active_pack = None
        s.queue.clear()
    DRAFT.running = True
    DRAFT.open_pack(1)
    await interaction.response.send_message(
        "Draft spuštěn! Posílám první packy do seat kanálů…", ephemeral=True)
    for seat in DRAFT.seats:
        await send_pack_to_seat(seat)


@client.tree.command(name="draft_next", description="ADMIN: otevře další pack")
async def draft_next(interaction: discord.Interaction):
    if not is_organizer(interaction):
        await interaction.response.send_message(
            "Tohle můžou spustit jen organizátoři (role Organizer).", ephemeral=True)
        return
    # ... zbytek příkazu zůstává beze změny ...
    if DRAFT.current_pack_number >= NUM_PACKS:
        await interaction.response.send_message("Všechny packy už proběhly, draft je u konce.", ephemeral=True)
        return
    if not DRAFT.round_finished():
        await interaction.response.send_message("Tenhle pack ještě není dokončený.", ephemeral=True)
        return
    DRAFT.open_pack(DRAFT.current_pack_number + 1)
    await interaction.response.send_message(f"Otevírám pack {DRAFT.current_pack_number}…", ephemeral=True)
    for seat in DRAFT.seats:
        await send_pack_to_seat(seat)


@client.tree.command(name="pick", description="Vyber kartu z aktuálního packu podle čísla")
@app_commands.describe(cislo="Číslo karty z aktuálního packu")
async def pick(interaction: discord.Interaction, cislo: int):
    seat = DRAFT.seat_by_channel(interaction.channel_id)
    if seat is None:
        await interaction.response.send_message("Tenhle příkaz použij ve svém seat kanálu.", ephemeral=True)
        return
    if not seat.has_active():
        await interaction.response.send_message("Nemáš teď žádný aktivní pack.", ephemeral=True)
        return
    if cislo < 1 or cislo > len(seat.active_pack.cards):
        await interaction.response.send_message(
            f"Neplatná volba. Vyber číslo od 1 do {len(seat.active_pack.cards)}.", ephemeral=True)
        return

    seat_index = seat.number - 1
    chosen, newly_active = DRAFT.pick(seat_index, cislo - 1)

    rf = " [RF]" if chosen.get("rf") else ""
    player_name = interaction.user.display_name
    url = build_fabrary_url(seat.pool, player_name)

    hlava = (
        f"✅ Vybral sis: **{short_name(chosen['name'])}{rf}**\n\n"
        f"__**Tvůj dosavadní pool ({len(seat.pool)}):**__\n"
        f"{format_pool(seat.pool)}"
        f"{pool_summary(seat.pool)}"
    )
    odkaz = f"\n\n📦 [Zobrazit celý balíček na Fabrary]({url})"

    # 1) balíčky dalším seatům (důležité)
    for s in newly_active:
        await send_pack_to_seat(s)
    # 2) potvrzení hráči s pojistkou na 2000 znaků
    try:
        if len(hlava) + len(odkaz) <= 2000:
            await interaction.response.send_message(hlava + odkaz)
        else:
            await interaction.response.send_message(hlava[:1990])
            await interaction.followup.send(odkaz.strip())
    except Exception as e:
        print("Nepodařilo se poslat potvrzení picku:", e)


    # info o dokončení kola → do admin kanálu draft-pod-1, ne hráči
    if DRAFT.round_finished():
        zprava_admin = (
            f"🏁 Pack {DRAFT.current_pack_number} je dokončen! "
            + ("Draft skončil." if DRAFT.current_pack_number >= NUM_PACKS
               else "Otevři další pomocí `/draft_next`.")
        )
        admin_channel = client.get_channel(ADMIN_CHANNEL_ID) if ADMIN_CHANNEL_ID else None
        if admin_channel:
            await admin_channel.send(zprava_admin)
        else:
            print("Pozor: kanál draft-pod-1 nenalezen, hlášku o dokončení nemám kam poslat.")


@client.tree.command(name="resend", description="Znovu pošle aktuální balíček do tohoto seat kanálu")
async def resend(interaction: discord.Interaction):
    seat = DRAFT.seat_by_channel(interaction.channel_id)
    if seat is None:
        await interaction.response.send_message(
            "Tenhle příkaz použij ve svém seat kanálu.", ephemeral=True)
        return
    if not seat.has_active():
        await interaction.response.send_message(
            "Tenhle seat teď nemá žádný aktivní balíček k zobrazení.", ephemeral=True)
        return
    # potvrzení jen volajícímu, ať nezahltíme kanál
    await interaction.response.send_message("Posílám aktuální balíček znovu… 🔄", ephemeral=True)
    await send_pack_to_seat(seat)

# ---------- PŘIHLAŠOVACÍ PANEL ----------
SEAT_ROLE_PREFIX = "Draftpod-1 Seat-"   # role se jmenují "Draftpod-1 Seat-1" atd.


def seats_taken():
    return sum(1 for s in DRAFT.seats if s.player_id is not None)


def first_free_seat():
    for s in DRAFT.seats:
        if s.player_id is None:
            return s
    return None


def seat_of_player(user_id):
    for s in DRAFT.seats:
        if s.player_id == user_id:
            return s
    return None


def panel_text():
    lines = [f"## 🎴 Přihlášení do draftu ({seats_taken()}/{NUM_SEATS})", ""]
    for s in DRAFT.seats:
        who = f"<@{s.player_id}>" if s.player_id else "_volné_"
        lines.append(f"**seat-{s.number}:** {who}")
    return "\n".join(lines)


async def get_seat_role(guild, seat_number):
    name = f"{SEAT_ROLE_PREFIX}{seat_number}"
    return discord.utils.get(guild.roles, name=name)


class JoinPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)   # trvalý panel

    @ui.button(label="Přihlásit do draftu", style=discord.ButtonStyle.success,
               custom_id="draft_join")
    async def join(self, interaction: discord.Interaction, button: ui.Button):
        if seat_of_player(interaction.user.id):
            await interaction.response.send_message("Už jsi přihlášený.", ephemeral=True)
            return
        seat = first_free_seat()
        if seat is None:
            await interaction.response.send_message("Draft je plný (8/8).", ephemeral=True)
            return
        role = await get_seat_role(interaction.guild, seat.number)
        if role is None:
            await interaction.response.send_message(
                f"Nenašel jsem roli `{SEAT_ROLE_PREFIX}{seat.number}`. Řekni organizátorovi.",
                ephemeral=True)
            return
        try:
            await interaction.user.add_roles(role)
        except discord.Forbidden:
            await interaction.response.send_message(
                "Nemám právo přidělit roli (zkontroluj Manage Roles a pořadí rolí).",
                ephemeral=True)
            return
        seat.player_id = interaction.user.id
        await interaction.response.edit_message(content=panel_text(), view=self)
        await interaction.followup.send(
            f"✅ Přihlášen do **seat-{seat.number}**. Kanál by se ti měl zobrazit.",
            ephemeral=True)

    @ui.button(label="Odhlásit z draftu", style=discord.ButtonStyle.danger,
               custom_id="draft_leave")
    async def leave(self, interaction: discord.Interaction, button: ui.Button):
        seat = seat_of_player(interaction.user.id)
        if seat is None:
            await interaction.response.send_message("Nejsi přihlášený.", ephemeral=True)
            return
        role = await get_seat_role(interaction.guild, seat.number)
        if role:
            try:
                await interaction.user.remove_roles(role)
            except discord.Forbidden:
                pass
        seat.player_id = None
        await interaction.response.edit_message(content=panel_text(), view=self)
        await interaction.followup.send(
            f"Odhlášen ze **seat-{seat.number}**.", ephemeral=True)


@client.tree.command(name="draft_panel", description="ADMIN: zobrazí přihlašovací panel")
async def draft_panel(interaction: discord.Interaction):
    if not is_organizer(interaction):
        await interaction.response.send_message(
            "Tohle můžou spustit jen organizátoři (role Organizer).", ephemeral=True)
        return
    await interaction.response.send_message(panel_text(), view=JoinPanel())

client.run(os.getenv("DISCORD_TOKEN"))