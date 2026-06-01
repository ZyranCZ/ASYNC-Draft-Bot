# :flower_playing_cards: ASYNC Draft Bot — v0.1

Bot pro **asynchronní draft** Flesh and Blood. Hráči draftují každý ve svém soukromém kanálu a **nemusí být online ve stejnou chvíli** — každý pickne, až se dostane ke slovu, a bot pošle zbytek balíčku dál.

- [Přehled karet v poolu](docs/TODO_1_prehled_poolu.md)
- [Identita balíčku](docs/TODO_2_balicek_identita.md)
- [Zachování bota](docs/TODO_3_perzistence.md)
- [Oprava duplicit v boosterch](docs/TODO_4_oprava_duplicit.md)

## :white_check_mark: Co už bot umí

**Načítání setu**
- Importuje Draftmancer `.txt` soubor (sekce Settings, CustomCards, Layouts i slot-pooly).
- Aktuální set OMEN: **209 karet, 18 layoutů, 10 slot-poolů.**

**Generování balíčků**
- Vygeneruje booster podle náhodného distribučního klíče:
•    itpipjychhuk (1000000) 
•    awsayojuhhlu (175000) 
•    rogepdbbacwb (35000) 
•    nzxilfwkhxqp (250000) 
•    dtowgefoyeco (43750) 
•    vsqrpqffzjcj (8750) 
•    dthapbfbbllz (1000000) 
•    hhcecaxzeaep (175000) 
•    wodrdfuzvouw (35000) 
•    lozypvsbctdm (250000) 
•    lphuqmuujdtd (43750) 
•    ivflyyaufnki (8750) 
•    zlqdlmjgdngc (1000000) 
•    lylotwqiqzhn (175000) 
•    xrdxlmdtiwzy (35000) 
•    jdtpdtrtdxje (250000) 
•    bvdyurqievuv (43750) 
•    xyonxyxzzyfw (8750)
- Respektuje `withReplacement` (počítá kopie jako fyzické karty).
- Označí Rainbow Foil karty `[RF]`.

**Balíček v Discordu**
- Pošle balíček jako galerii obrázků karet (přímo z fabrary.io, nic se nenahrává) + očíslovaný seznam karet jako text.
- Karty se vybírají číslem přes `/pick`.

**Motor draftu**
- 8 seatů, 3 balíčky po 14 kartách.
- Předávání zbytku balíčku sousedovi, fronta balíčků (nikdy nevidíš dva naráz).
- Střídání směru: balíček 1 doprava, balíček 2 doleva, balíček 3 doprava.

**Pool a export**
- Po každém picku bot potvrdí kartu a ukáže celý dosavadní pool.
- Rovnou nabídne klikací odkaz na **import balíčku do Fabrary**.

**Přihlašování**
- Tlačítkový panel `[Přihlásit do draftu]` / `[Odhlásit z draftu]` s počtem hráčů.
- Po přihlášení bot automaticky přidělí seat a roli → kanál se hráči zobrazí sám.

## :tools: Příkazy

**Pro hráče**
- `/pick [číslo]` — vybere kartu z aktuálního balíčku
- `/resend` — znovu pošle aktuální balíček (kdyby zmizel nebo nedorazil)
- `/ping` — ověří, že bot žije

**Pro organizátory** (role Organizer)
- `/draft_panel` — zobrazí přihlašovací panel
- `/draft_start` — spustí draft a otevře 1. balíček
- `/draft_next` — otevře další balíček (po dokončení předchozího)
- `/draft_clear` — smaže zprávy v seat kanálech (s potvrzením)

## :soon: Roadmapa

- **v0.7** — ukládání stavu (restart bota nezničí rozehraný draft)
- **v0.8** — trvalý provoz (bot běží nonstop, ne jen při zapnutém PC)
- **v0.9** — podpora jiného počtu hráčů než 8
- **v0.9.5** — víc draftů naráz
- **v1.0** — vše pohromadě, ostré nasazení

Drobnosti cestou: upozornění hráče při novém balíčku, kontrola, že pickuje správný hráč.

## :warning: Aktuální omezení (v0.1)

- Stav žije v paměti — **po restartu bota se rozehraný draft ztratí** (řešíme ve v0.7).
- Počítá s přesně **8 hráči** a jedním draftem naráz.


# 🗺️ DraftBot — Master soupis úprav

Kompletní přehled toho, co bota čeká. Spojuje tipy od komunity s tím, co jsme
naprojektovali, a doplňuje závislosti a rizika. Řazeno podle priority / pořadí.

Legenda stavu:
- ✅ HOTOVO (funguje v botu)
- 📝 K PROVEDENÍ (máš na to TODO dokument)
- 🔢 NAPROJEKTOVÁNO (rozmyšleno, čeká na realizaci)
- 💡 NÁPAD (ještě neprojektováno)

---

## ČÁST A — Připravené TODO

Pořadí: #1 → #2 → #3 (mají závislosti). TODO #4 je nezávislé — klidně první.

### 📝 TODO #1 — Finální přehled poolu po picku
- Zkrácené pitche (red)→(r), (yellow)→(y), (blue)→(b), bez rarity.
- Souhrn: počty pitchů 🔴🟡🔵 + equipment sloty Head/Chest/Arms/Legs
  (s vypsanými konkrétními kartami) + rozdělení podle slotů + řádek Rare/Mythic (RF).
- Pokrývá komunitní tipy: „lepší vypisování pitch", „quick přehled pitch/sloty".

### 📝 TODO #2 — Balíček s identitou + nový nadpis
- Nadpis: `Seat 4's Pack #1 — Pick #4` (origin seat + číslo packu + kolikátý pick).
- Balíček se mění z holého seznamu na objekt Pack (origin_seat, pack_number).
- Pokrývá komunitní tip: „lepší označení názvu boosteru".
- ZÁVISLOST: používá short_name z TODO #1 → dělat po #1.

### 📝 TODO #3 — Perzistence (uložení/obnova draftu)
- Stav do draft_state.json, atomický zápis (bezpečné i při souběhu picků), obnova po restartu.
- ZÁVISLOST: ukládá Pack objekty z TODO #2 → dělat po #2.
- Odblokovává dropdown picker (viz část B).
- Řeší známé riziko ztráty rozehraného draftu při restartu.

### 📝 TODO #4 — Oprava duplicitních karet v boosteru (BUG)
- V jednom boosteru se nesmí objevit tatáž karta 2× (mimo RF varianty).
- Úprava booster_generator.py: losovat z unikátních názvů + hlídat used_names.
- NEZÁVISLÉ na #1–#3 — můžeš udělat kdykoliv, klidně jako PRVNÍ.
- Ovlivňuje férovost draftu, věrné reálným print sheets. Detail viz část F.

---

## ČÁST B — Naprojektováno, čeká na realizaci

### 🔢 Dropdown picker karet (po perzistenci)
- Rozevírací seznam 14 karet pod balíčkem místo psaní /pick.
- Po výběru potvrzení „Vybral sis: Xxx — Potvrdit? Ano/Ne" (proti překliku).
- Ovládat smí jen hráč daného seatu; po picku se starý dropdown zneplatní.
- Musí být persistent (custom_id) → proto až po perzistenci.
- /pick zůstává jako záloha.
- Pokrývá komunitní tip: „uživatelsky přívětivější pickování".

---

## ČÁST C — Automatizace draftu (komunitní tipy + naše návrhy)

### 💡 Ping role Organizer při 8/8 přihláškách
- Když se přihlásí 8. hráč, bot pingne roli Organizer „draft je plný, můžeš spustit".
- K prozkoumání: zda rovnou spustit draft automaticky botem (bez ručního /draft_start).
- Rozhodnout: plné automatické spuštění vs. jen upozornění (doporučuji upozornění —
  organizátor má poslední slovo, může chtít zamíchat seaty apod.).

### 💡 Automatické otevírání packu 2 a 3
- Teď musí organizátor ručně /draft_next. Zvážit: po dokončení packu otevřít
  další automaticky.
- Pozor (důvod, proč to teď je ručně): dokumentace draftu chtěla, aby další pack
  otevíral výhradně organizátor. Rozhodnout, jestli to chceme změnit, nebo nechat
  ruční s tím, že přibude jen upozornění „pack dokončen, můžeš otevřít další".

### 💡 Rozsazení do draft-pod-1 při startu draftu
- Při /draft_start poslat do draft-pod-1 textové schéma rozsazení (4 proti 4)
  se směry pro všechny 3 packy, kde místo Seat X budou @jména hráčů.
- Formát (v code blocku, ať drží tvar):
  PACK 1 →  S1▶S2▶S3▶S4▼ / ▲S8◀S7◀S6◀S5
  PACK 2 ←  opačně
  PACK 3 →  jako PACK 1
- Pozn.: schéma bude jako BĚŽNÝ text (ne code block), takže @jména fungují jako
  klikací pingy. Zarovnání se neřeší — je to pár řádků se šipkami, ne mřížka,
  takže svislé lícování není potřeba. Znaky ▶ ◀ ▼ ▲ se v běžném textu zobrazí OK.

---

## ČÁST D — Organizátorské nástroje

### 💡 Shuffler seatů
- Zamíchat pořadí hráčů před startem (teď je pořadí dle přihlášení).
- Jen ve fázi „přihlášeni, ale draft neběží"; musí přehodit i role Draftpod-1 Seat-N.
- Manuální přeřazení už možné je.

### 🔢 Live přehled stavu / buzerovač v draft-pod-1
- Jedna trvale EDITOVANÁ zpráva v draft-pod-1 (bot ji přepisuje, neposílá novou).
- Ukazuje stav všech seatů. Přesný formát:
  `🎴 **Stav draftu — Pack 1**`
  `⏳ Seat 1: <@id> ještě vybírá — balíček dorazil <t:UNIX:R>`
  `✅ Seat 3: <@id> čeká na další pack`
- Discord timestamp `<t:UNIX:R>` se vykreslí jako „před 5 minutami" a aktualizuje
  se SÁM u každého diváka — bot nemusí editovat periodicky, jen při akci.
- Bot edituje zprávu jen ve dvou okamžicích: (1) když seatu pošle balíček
  → zapíše nový timestamp + stav „ještě vybírá"; (2) když seat pickne
  → přepne na „čeká na další pack".
- DŮLEŽITÉ: u zmínek <@id> potlačit notifikace přes allowed_mentions
  (jména budou klikací a vidět, ale nikoho to nepingne při každé editaci).
- ZÁVISLOST: drží ID jedné zprávy → po restartu ho musí znát → čistší
  PO perzistenci (TODO #3), kde se ID uloží do stavu.
- Volitelně přidat: číslo packu se mění podle current_pack_number; lze doplnit
  i Pick # nebo délku fronty.

### 💡 Export všech decklistů pro organizátora
- Jeden příkaz vypíše/pošle Fabrary odkazy pro všech 8 hráčů najednou.
- Export jednoho už umíme, tohle je smyčka přes všechny.

### 🔢 Zamknout přihlašovací panel po startu draftu
- Po /draft_start tlačítka [Přihlásit]/[Odhlásit] zašednou + text „Draft probíhá".
- Brání tomu, aby si hráč omylem uvolnil seat během běžícího draftu.
- Kód na tohle už máme připravený z dřívější diskuze.

### 💡 Pauza / obnovení / force-pick
- /draft_pause, /draft_resume, /draft_force-pick za neaktivního hráče.
- Z původní dokumentace; force-pick odblokuje zaseklý asynchronní draft.

---

## ČÁST E — Export / Fabrary

### 💡 Předvyplněný název balíčku ve Fabrary
- Fabrary import umí přednastavit název decku.
- Formát např. „ASYNC Draft 01/06/2026" (datum draftu).
- Zjistit přesný parametr URL pro název a doplnit do build_fabrary_url.

---

## ČÁST F — Známá rizika / bugy (ošetřit, až nastane)

### 🐞 BUG: duplicitní karta v jednom boosteru → vyřešeno v TODO #4
- Stává se reálně. Příklad: 2× Holo Shield (blue) v jednom packu.
- PŘÍČINA (dvojí): (1) karta má ve slotu víc kopií (Holo Shield = 4 kopie ve
  slotu LightningIllusionist) a generátor losoval z rozbaleného seznamu kopií,
  takže mohl vytáhnout 2 kusy téže karty z TÉHOŽ slotu; (2) karta je často ve
  více slotech, takže ji mohly vytáhnout dva různé sloty. Oprava řeší obojí.
- OPRAVA: losovat z UNIKÁTNÍCH názvů ve slotu + hlídat, že se název v boosteru
  neopakuje (set used_names). RF sloty se nehlídají.
- VÝJIMKA: RF varianty smí být duplicitní vůči normální verzi (RFCommon/RFRare/
  RFMythic se z kontroly vynechá).
- KONTEXT: tohle je VĚRNÉ reálným print sheets — karty se stříhají z archů a dvě
  stejné se na jednom boosteru nikdy nesejdou. Oprava fyzický model neopouští,
  naopak ho vystihuje přesněji.
- OVĚŘENO: 3000 boosterů po opravě → 0 duplicit (mimo RF), každý booster 14 karet.
- STAV: má samostatné TODO #4 (úprava booster_generator.py, nezávislé na #1–#3).

### ⚠️ Limit 2000 znaků u zprávy po picku
- Plný pool (~42 karet) + Fabrary URL může přesáhnout 2000 znaků a zpráva spadne.
- Je to na hraně — projde to často, ale ne vždy (záleží na délce názvů).
- Řešení, až nastane: poslat URL jako druhou zprávu, nebo zkrátit jinak.

### ⚠️ Při novém setu zkontrolovat EXCLUDED_SLOTS
- Rozdělení podle slotů se učí z TXT samo, ale „nezajímavé" kategorie
  (Equipment, rare, Mythic, RF*) jsou pevný seznam. Nový set s novou speciální
  kategorií → zkontrolovat/doplnit EXCLUDED_SLOTS (jednořádková úprava).

---

## ČÁST G — Větší verze (roadmapa)

- **v0.7** — perzistence (= TODO #3)
- **v0.8** — hosting (bot běží nonstop, ne jen při zapnutém PC)
- **v0.9** — podpora jiného počtu hráčů než 8
- **v0.9.5** — víc draftů naráz
- **v1.0** — vše pohromadě, ostré nasazení

---

## ČÁST H — Dál / sen (zatím neřešit)

- Statistiky poolu (rozložení pitchů, křivka nákladů).
- Log picků (kdo co kdy vzal) — pro řešení sporů.
- DM hráči navíc ke zprávě v kanálu (lidi přehlížejí kanály).
- Uvítací zpráva / legenda pitchů v seat kanálu pro nováčky.
- Turnajová část po draftu: párování, výsledky, standings.
- Více formátů draftu, lokalizace CZ/EN.

---

## Co jsem doplnil oproti tvému seznamu (nebylo tam)

- Rozdělení tipů podle závislostí (co na čem stojí, v jakém pořadí).
- ČÁST F — známá rizika (limit 2000 znaků, EXCLUDED_SLOTS).
- Zamknutí přihlašovacího panelu po startu (padlo v diskuzi, kód připraven).
- Pauza/resume/force-pick (z původní dokumentace).
- Upozornění u automatizací: proč je teď otevírání packu ručně (záměr z dokumentace).
- Roadmapa verzí a „sen" sekce.

> Verze 0.1 — testovací. Nápady a bug reporty vítány! :raised_hands:
