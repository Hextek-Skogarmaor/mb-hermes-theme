# Mora Bygg theme för Hermes Desktop

Mora Byggs design v1 som tema i Hermes Desktop: Mora-blå för handling och fokus, bläck för text, Source Sans 3. Ljust och mörkt läge.

Alla värden kommer från `MoraBygg/Design/DESIGN.md` (mb-Agentic). Det här repot bara läser därifrån.

## Installera

```bash
./install.sh              # bygg från Design-mappen och installera
./install.sh --prebuilt   # installera dist/plugin.js som den är (Design-mappen behövs inte)
```

Design-mappen hämtas från `~/Mora Bygg/mb-Agentic/MoraBygg/Design`. Ligger den någon annanstans: `MORA_DESIGN=/sökväg ./install.sh`.

Pluginen hamnar i `$HERMES_HOME/desktop-plugins/mora-bygg-theme/` (standard `~/.hermes`). Hermes Desktop laddar den inom några sekunder, utan omstart. Första gången väljer den sig själv en gång, sedan gäller användarens val i Settings → Appearance. ⌘K → **Mora Bygg: Aktivera tema** byter tillbaka. Ljust/mörkt väljs som vanligt i appen.

## Uppdatera efter en designändring

```bash
./install.sh && git add dist/plugin.js && git commit -m "Bygg om från Mora Bygg DESIGN.md"
```

`dist/plugin.js` genereras. Redigera den aldrig för hand; ändra `build.py` eller DESIGN.md.

Bygget har en kontrastspärr: om någon text/yta-kombination hamnar under WCAG AA (4,5:1, kontroller 3:1) skrivs ingen fil.

## Ljust läge (DESIGN.md v1, token för token)

| Yta | Token |
|---|---|
| Chatt/sidans bakgrund | `canvas #F7F7FB` |
| Sidomeny, kort, popovers | `surface #FFFFFF` |
| Handling, fokus, aktiv flik | `primary #2E3192`, vit text |
| Valt läge, egen chattbubbla | `primarySoft #EAEAF4` med blå text |
| Text / dämpad text | `ink #231F20` / `textMuted #686570` |
| Linjer / kontrollkanter | `border #DCDCE4` / `borderStrong #8B8A96` |
| Status | `ok #1D6B3A`, `danger #B3261E` |

Sämsta par: kontrollkant mot `canvas` 3,18:1 (krav 3:1). All text ≥ 4,5:1.

## Mörkt läge (härlett, inte en del av DESIGN.md ännu)

DESIGN.md säger att mörkt läge inte är definierat. Det här är ett förslag som **bara** använder befintliga tokens, blandade i sRGB:

| Roll | Härledning | Värde |
|---|---|---|
| Bakgrund, sidomeny | `ink` | `#231F20` |
| Kort | `ink` + 5 % `canvas` | `#2E2A2B` |
| Popover, egen chattbubbla | `ink` + 8 % `canvas` | `#343032` |
| Text | `canvas` | `#F7F7FB` |
| Dämpad text | `canvas` + 40 % `ink` | `#A2A1A3` |
| Linjer | `ink` + 15 % `canvas` | `#433F41` |
| Kontrollkanter | `ink` + 45 % `canvas` | `#828083` |
| Mora-blå, ljusare | `primary` + 60 % `canvas` | `#A7A8D1`, text på den = `ink` |
| Valt läge | `ink` + 45 % `primary` | |
| Status | `ok` + 45 %, `warning` + 45 %, `danger` + 50 % `canvas` | |

Sämsta par: kontrollkant mot kort 3,62:1. All text ≥ 4,5:1. Om Mora Bygg vill ha mörkt läge som standard bör värdena flyttas in i DESIGN.md (arkivera, lint 0/0, bygg exporter) och läsas därifrån.

## Följer DESIGN.md

- Inga gradienter, ingen glans, inga mönster. Bara platta ytor och 1 px linjer.
- En accent: Mora-blå. Statusfärger bara för status.
- Logotypen används inte (ingen godkänd negativ version finns, och appen har ingen logoplats).
- Source Sans 3 är inbäddad (woff2, OFL), inga typsnitt hämtas från nätet. Kod: JetBrains Mono, som följer med appen.

## Vad temat är beroende av i appen

Färgerna går genom det publika `THEMES_AREA` / `DesktopTheme`-kontraktet och är stabila. `customCSS` använder dessutom:

- `--theme-mix-*`: satta till 100 % så att appen inte blandar ytorna mot sin egen grå
- `--ui-success`, `--ui-green`, `--ui-red`: låsta till Mora Byggs statusfärger (appen drar annars grönt mot accenten)
- `:root[data-hermes-mode='dark']`: statusfärger i mörkt läge

Flyttar en Hermes-uppdatering dessa hakar blir ytorna något gråare, men temat fungerar. Jämför med `apps/desktop/src/styles.css` och `src/themes/context.tsx`.

## Licenser

Source Sans 3 och JetBrains Mono: SIL Open Font License 1.1 (se `LICENSES/`). Temakod © Hextek AB, byggt för Mora Bygg AB.
