# :flower_playing_cards: ASYNC Draft Bot — v0.1

Bot pro **asynchronní draft** Flesh and Blood. Hráči draftují každý ve svém soukromém kanálu a **nemusí být online ve stejnou chvíli** — každý pickne, až se dostane ke slovu, a bot pošle zbytek balíčku dál.

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

> Verze 0.1 — testovací. Nápady a bug reporty vítány! :raised_hands:
