# portflow-api-python

Scripts die evaluaties van studenten ophalen uit de Portflow API (portfolio.drieam.app) en overzichtelijk tonen in de terminal of exporteren naar mappen.

## Scripts

| Script | Wat het doet |
|---|---|
| `portflow.py` | Hoofdscript. Toont evaluaties van één student of een tabel voor een groep studenten, een lijst met evaluaties die jij nog moet beoordelen, en weekgrafieken. Bevat ook beheeropties om studentenlijsten in `.env` te vullen. |
| `portflow_export_full.py` | Exporteert van één student alle evaluaties, bijlagen en opmerkingen van het huidige semester naar een mappenstructuur. |
| `export_single_student.py` | Variant van `portflow_export_full.py` die standaard je coachstudenten uit `.env` als keuzelijst gebruikt. |
| `evaluaties.py` | Losse versie van de lijst met openstaande evaluatieverzoeken (zit ook in `portflow.py`). |
| `graph.py` | ASCII-tijdlijn van de evaluaties van één student. |
| `retrieve_token.py` | Haalt een nieuw bearer token op via een browservenster en slaat het op in `.env` (zit ook in `portflow.py`). |

De tekstbestanden `vaardigheden.txt`, `beroepstaken.txt` en `beroepsrollen.txt` zijn naslaglijsten met codes; de scripts lezen ze niet.

## Vereisten

- Python 3.10+
- Python-packages:

| Package | Nodig voor | Verplicht |
|---|---|---|
| `requests` | Alle API-aanroepen (alle scripts) | ja |
| `openpyxl` | Studenten importeren uit Excel-bestanden (`portflow.py --admin`) | nee |
| `playwright` | Token ophalen via een browservenster (`portflow.py` bij een verlopen token, en `retrieve_token.py`) | nee |

- Voor `playwright`: Google Chrome, of anders Playwright Chromium (`python3 -m playwright install chromium`).

Alles installeren:

```bash
pip install requests openpyxl playwright
```

Alleen het minimum:

```bash
pip install requests
```

`portflow.py` meldt bij het starten of `requests` of `openpyxl` ontbreekt. Zonder `openpyxl` werkt alles behalve de Excel-import. Ontbreekt `playwright` en kies je voor het browservenster, dan biedt het script aan het te installeren; je kunt het token ook altijd plakken.

## Configuratie (`.env`)

Alle scripts lezen hun instellingen uit een `.env`-bestand in dezelfde map als het script. Bij `portflow.py` kun je een ander bestand kiezen met `--config pad/naar/.env`. Kopieer `.env.example` naar `.env` en vul de waarden in.

### Variabelen

| Variabele | Gebruikt door | Beschrijving |
|---|---|---|
| `PORTFLOW_BEARER_TOKEN` | alle scripts | JWT bearer token voor de Portflow API. Zie [Bearer token](#bearer-token). Ontbreekt het of is het verlopen, dan vraagt `portflow.py` om een nieuw token en slaat het zelf op. |
| `PORTFLOW_SEMESTER_START` | alle scripts | Eerste dag van het semester, `YYYY-MM-DD`. Evaluaties buiten het semester worden niet getoond. `portflow.py` vraagt erom als het ontbreekt en slaat het antwoord op; de andere scripts gebruiken dan `2026-02-12`. |
| `PORTFLOW_SEMESTER_END` | alle scripts | Laatste dag van het semester, `YYYY-MM-DD`. Zelfde gedrag; standaard in de andere scripts is `2026-06-30`. |
| `PORTFLOW_OWN_PORTFOLIO_ID` | `portflow.py`, `evaluaties.py` | ID van je eigen portfolio. Je vindt het in de URL als je je eigen portfolio opent, bijv. `https://portfolio.drieam.app/portfolio/23588/...`. Nodig voor de lijst met evaluaties die je moet beoordelen, voor de naam van de beoordelaar bij openstaande evaluaties en voor beheeroptie 6 en 7. `evaluaties.py` vraagt erom als het ontbreekt. |
| `PORTFLOW_COACH_STUDENTS_JSON` | `portflow.py`, export-scripts | Je coachstudenten. Zie [Studentenlijsten](#studentenlijsten). |
| `PORTFLOW_TRIBE_STUDENTS_JSON` | `portflow.py` | Alle studenten in je tribe. Zelfde formaat. |
| `PORTFLOW_GILDE_STUDENTS_JSON` | `portflow.py` | Alle studenten in je gilde. Zelfde formaat. |
| `PORTFLOW_EXCLUDED_REVIEWERS` | `portflow.py` | Komma-gescheiden namen van beoordelaars van wie beoordeelde evaluaties overal worden weggelaten (bijv. een student die als beoordelaar optrad terwijl dat niet mag). Zonder deze variabele geldt de standaardnaam in de code; zet de variabele om dat te overschrijven. |
| `PORTFLOW_SECTION_ID` | `export_single_student.py` | Section-ID voor `--students-source section`. Standaard `72086`. |

### Studentenlijsten

`PORTFLOW_COACH_STUDENTS_JSON`, `PORTFLOW_TRIBE_STUDENTS_JSON` en `PORTFLOW_GILDE_STUDENTS_JSON` zijn JSON-lijsten met één object per student. De lijst mag over meerdere regels lopen:

```env
PORTFLOW_COACH_STUDENTS_JSON=[
    {"name": "Voornaam Achternaam", "start_date": null, "semester": "4", "tribe": "Tribe A", "gilde": "FE", "coach": "Peter"},
    {"name": "Andere Student",      "start_date": "2026-10-01", "semester": "3", "tribe": "Tribe A", "gilde": "CS", "coach": "Peter"},
    {"separator": true},
    {"name": "Derde Student"}
]
```

Alleen `name` is verplicht; ontbrekende velden blijven leeg.

| Veld | Waarde | Betekenis |
|---|---|---|
| `name` | tekst | Volledige naam precies zoals in Portflow. |
| `start_date` | `"YYYY-MM-DD"` of `null` | Eigen startdatum voor deze student; vervangt `PORTFLOW_SEMESTER_START` bij het filteren. |
| `semester` | tekst, bijv. `"3"` | Kolom *Sem* in de tabel. Bij `"3"` en `"4"` wordt de cel groen als de student aan de semestereisen voldoet (zie [Kleuren](#kleuren-in-de-tabel)). |
| `tribe` | tekst | Kolom *Tribe*; ook gebruikt om de keuzelijst bij één student te groeperen. |
| `gilde` | tekst, bijv. `"FE"` | Kolom *Gilde*. |
| `coach` | tekst | Kolom *Coach* in de tribe- en gildetabel. |
| `gildemeester` | tekst | Kolom *Gildemeester* in de gildetabel en in de evaluatielijst voor gildestudenten. |
| `resultaat` | `"geslaagd"` of `"gezakt"` | Kleurt de *Sem*-cel donkergroen of rood. |
| `separator` | `true` | Geen student maar een scheidingslijn in de tabel. |

Let op: bij het starten voegt `portflow.py` aan elke student zonder `coach` het veld `"coach": ""` toe en schrijft de lijst daarvoor opnieuw weg in `.env`.

## `portflow.py`

### Starten

```bash
python3 portflow.py
```

Het script toont het semester, controleert het token en vraagt dan via menu's wat je wilt zien. Na het overzicht stopt het script. Na een beheeroptie keer je terug naar het hoofdmenu; daar stop je met `q`.

Veelgebruikte aanroepen die de menu's overslaan:

```bash
# Tabel met al je coachstudenten, inclusief nog niet beoordeelde evaluaties (?)
python3 portflow.py --aantal meer --lijst coach --vraagtekens 1

# Eén student: de derde uit je coachlijst
python3 portflow.py --aantal 1 --lijst coach --student 3

# Tabel voor een presentatie: namen en tribe/semester/gilde onherkenbaar
python3 portflow.py --aantal meer --lijst coach --anoniem
```

### Opties

| Optie | Betekenis |
|---|---|
| `--aantal {1,meer}` | Kies direct *één student* of *meerdere studenten*. |
| `--lijst {alles,coach,tribe,gilde}` | Kies direct de groep: `alles` = alle studenten die hun portfolio met je delen; `coach`, `tribe`, `gilde` = de lijst uit `.env`. Wordt genegeerd als die lijst leeg is. |
| `--student N` | Kies direct de N-de student uit de lijst (alleen met `--aantal 1`). |
| `--vraagtekens 1` | Toon ook ingediende maar nog niet beoordeelde evaluaties, als `?`. |
| `--verberg KOLOMMEN` | Verberg kolommen in de tabel, komma-gescheiden: `Tribe`, `Semester`, `Gilde` of `alles`. |
| `--anoniem` | Vervang namen (en tribe, semester, gilde) door sterretjes, bijv. bij een screenshare. |
| `--admin` | Toon de beheeropties in het hoofdmenu (zie [Beheer](#beheer---admin)). |
| `--config BESTAND` | Gebruik een ander `.env`-bestand. |
| `--debug-api` | Log alle API-aanroepen met antwoord naar `api_debug_log.jsonl`. |
| `--debug-pending` | Log per evaluatie waarom die wel of niet getoond wordt naar `pending_debug.json`. |
| `--dump-schema` | Schrijf alle gevonden API-velden met voorbeeldwaarden naar `schema_inventory.txt`. |

### Menu's

**Hoofdmenu:** *1) Één student* of *2) Meerdere studenten*.

**Één student**: kies uit alle gedeelde portfolio's, uit je coach-, tribe- of gildelijst (als die gevuld is), of zoek op voornaam. Je ziet:

- de tabelrij van de student (zie [De tabel](#de-tabel)) met daaronder een weekgrafiek;
- behaalde evaluaties per vaardigheid, met niveau, initialen van de beoordelaar en datum;
- behaalde beroepstaken (HBO-i code, bijv. `SW-RE`);
- met `--vraagtekens 1`: ingediende evaluaties en beroepstaken die nog niet beoordeeld zijn. Een ingeleverd eindassessment (één verzoek voor alle 10 vaardigheden) staat als één regel *Assessment ingeleverd*.

**Meerdere studenten**:

| Keuze | Wat je ziet |
|---|---|
| Tabel met alle studenten die hun portfolio met mij hebben gedeeld | Tabel voor iedereen die zijn portfolio met je deelt. |
| Tabel met al mijn coach-/tribe-/gildestudenten | Tabel voor de lijst uit `.env` (alleen als die gevuld is), in de volgorde van `.env`. De tribe- en gildetabel hebben een extra kolom *Coach*, de gildetabel ook *Gildemeester*. In de tribe- en gildetabel staan studenten van wie je het portfolio niet kunt zien met `n/b`. |
| Evaluaties die ik nog moet beoordelen (coachstudenten) | Genummerde lijst van openstaande evaluatieverzoeken aan jou van je coachstudenten, met de vaardigheden en zelfgekozen niveaus. Kies een nummer voor de details. |
| Evaluaties die ik nog moet beoordelen (gildestudenten) | Hetzelfde voor alle andere studenten die je een verzoek stuurden, met kolommen *Coach* en *Gildemeester*. |
| Grafieken voor alle studenten die ik coach | Per coachstudent een weekgrafiek. |

### De tabel

Per student een rij met de tien vaardigheden (`OC`, `KO`, `JKO`, `KPM`, `PL`, `BD`, `SW`, `FO`, `PH`, `RE`), een kolom *Beroepstaken* en de kolommen *Tribe*, *Sem* en *Gilde*. In een vaardigheidscel staan de behaalde niveaus, bijv. `2, 1`; met `--vraagtekens 1` ook `?` voor evaluaties die nog wachten op beoordeling. *Beroepstaken* telt de beoordelingen per niveau, bijv. `3x2, 1x1`. Onder de tabel staat een weekgrafiek van alle evaluaties.

```text
Naam         | OC | KO | JKO | KPM | PL   | BD | SW   | FO | PH   | RE | Beroepstaken | Tribe   | Sem | Gilde
-----------------------------------------------------------------------------------------------------------------
Student 01   | 2  | 2  | 1   | 2   | 2    | 2  | 2, 1 | 2  | 3, 1 | 3  | 2x2, 1x1     | Tribe A | 4   | FE
Student 02   |    |    |     |     | 1    | 1  | 1, 2 |    | 2, 2 |    |              | Tribe A | 3   | CS
Student 03   |    |    | ?   |     |      |    | 3    | 2  |      |    | 1x?          | Tribe B | 3   | FE
```

#### Kleuren in de tabel

- **Rood (vaardigheidscellen):** geen enkele evaluatie voor OC, KO, JKO én KPM.
- **Oranje:** geen enkele evaluatie voor alle zes van PL, BD, SW, FO, PH en RE.
- **Geel:** vier of vijf van die zes zijn leeg.
- **Blauw:** de cel bevat een `?`.
- **Sem groen:** de student voldoet aan de eisen van het semester.
  - Semester 3: elke vaardigheid minstens 2 beoordelingen van minstens niveau 1, waarvan minstens 2 op niveau 2, en minstens 6 beroepstaken op niveau 1.
  - Semester 4: elke vaardigheid minstens 2 beoordelingen van minstens niveau 1, waarvan minstens 8 op niveau 2 (inclusief KPM), en minstens 4 beroepstaken op niveau 2.
- **Sem donkergroen / rood:** `resultaat` is `geslaagd` of `gezakt`.

Met `--anoniem` worden de *Sem*-kleuren niet getoond.

#### Wat telt mee

- Alleen evaluaties binnen het semester (of vanaf de `start_date` van de student).
- Beoordeelde zelfevaluaties worden niet getoond.
- Beoordelingen van namen in `PORTFLOW_EXCLUDED_REVIEWERS` worden overgeslagen.
- Openstaande `?` van een eindassessment worden in de tabel niet getoond.

### Beheer (`--admin`)

Met `--admin` krijgt het hoofdmenu extra keuzes om de studentenlijsten in `.env` te vullen:

| Keuze | Wat het doet | Nodig |
|---|---|---|
| 3 | Lees een studenten-Excel, kies een coach en zet diens studenten in `PORTFLOW_COACH_STUDENTS_JSON`. | studenten-Excel |
| 4 | Lees een studenten-Excel, kies een gilde en zet die studenten in `PORTFLOW_GILDE_STUDENTS_JSON`. | studenten-Excel |
| 5 | Kies een student uit alle gedeelde portfolio's en zet hem in een lijst naar keuze. | |
| 6 | Kies een student die jou een evaluatieverzoek stuurde en zet hem in een lijst naar keuze. | `PORTFLOW_OWN_PORTFOLIO_ID` |
| 7 | Hetzelfde, maar alleen studenten die nog niet in je coach- of gildelijst staan. | `PORTFLOW_OWN_PORTFOLIO_ID` |
| 8 | Vul semester, tribe en gilde aan voor studenten die al in een van de drie lijsten staan. | studenten-Excel |
| 9 | Lees een gildemeester-Excel, kies een gildemeester en zet diens studenten in `PORTFLOW_GILDE_STUDENTS_JSON`. | gildemeester-Excel |
| 10 | Lees een Excel met ontbrekende coachstudenten en voeg ze toe aan `PORTFLOW_COACH_STUDENTS_JSON`. | Excel ontbrekende coachstudenten |

Het script zoekt de Excel-bestanden (`.xlsx`) in de map van het script en herkent ze aan de kolomkoppen (de kopregel hoeft niet op rij 1 te staan). Passen meerdere bestanden, dan vraagt het welk je wilt gebruiken.

| Soort | Vereiste kolommen |
|---|---|
| studenten-Excel | `Nummer`, `Naam`, `Email`, `Semester`, `Project`, `Coach`, `Gilde voorkeur` |
| gildemeester-Excel | `Student`, `Coach`, `Semester`, `Gildemeester` |
| Excel ontbrekende coachstudenten | `Nummer`, `Naam`, `Project`, `Gilde`, `Sem` |

## Bearer token

De scripts hebben een bearer token nodig. Dat is een JWT dat ongeveer 2 uur geldig is.

### Vanuit `portflow.py`

Is het token in `.env` leeg of verlopen, dan vraagt `portflow.py` hoe je een nieuw token wilt ophalen:

1. **Via een browservenster**: opent Chrome en haalt het token automatisch op, net als `retrieve_token.py` hieronder.
2. **Token plakken**: haal het token zelf op (zie [Handmatig](#handmatig)) en plak het. Je kunt het token ook direct bij de keuzevraag plakken.

Het nieuwe token wordt altijd automatisch opgeslagen als `PORTFLOW_BEARER_TOKEN` in `.env`.

### `retrieve_token.py`

```bash
python3 retrieve_token.py [--config pad/naar/.env] [--timeout 300]
```

Het script opent een Chrome-venster met de Portflow-pagina in Canvas. Log zo nodig in. Zodra de pagina een API-request met een `Authorization: Bearer ...`-header doet, wordt het token gecontroleerd tegen `/api/v1/dashboard` en opgeslagen als `PORTFLOW_BEARER_TOKEN` in `.env`. Het venster sluit daarna vanzelf.

- Het browserprofiel staat in `.browser-profile/` (in `.gitignore`), zodat je meestal niet opnieuw hoeft in te loggen.
- `--timeout`: maximaal aantal seconden wachten op een token (standaard 300).
- Bij het starten toont het script de Python-versie, de versies van `requests` en `playwright` en de gevonden browser. Ontbreekt iets, dan biedt het aan het te installeren.

### Handmatig

1. Log in op [Portflow via Canvas](https://canvas.hu.nl/courses/51659/external_tools/1134) met je HU-account.
2. Open de **Inspector** in je browser (rechtermuisknop → Inspecteren, of `F12` / `Cmd+Option+I`).
3. Ga naar het tabblad **Network** (Netwerk).
4. Filter op `dashboard`.
5. Herlaad de pagina (`F5` / `Cmd+R`).
6. Klik op het eerste `dashboard`-verzoek.
7. Zoek in **Headers** naar `Authorization:`.
8. Kopieer de waarde achter `Bearer ` (alleen het token).

De screenshot toont dit in Safari (het token in de screenshot is ongeldig):

![Screenshot](docs/images/portflow-dashboard-redacted.png)

Plak het token in `portflow.py` als daarom gevraagd wordt, of zet het zelf in `.env`:

```env
PORTFLOW_BEARER_TOKEN=eyJraWQiOi...
```

`portflow_export_full.py`, `export_single_student.py` en `graph.py` accepteren het token ook als `--token <token>`.

## Overige scripts

### `portflow_export_full.py` en `export_single_student.py`

```bash
python3 portflow_export_full.py [--output-dir MAP] [--students-source {section,shared}] [--section-id ID] [--token TOKEN]
python3 export_single_student.py [--output-dir MAP] [--students-source {coach,section,shared}] [--section-id ID] [--token TOKEN]
```

| Optie | Betekenis |
|---|---|
| `--output-dir` | Basismap; de export komt in `<MAP>/exports/` (standaard de huidige map). |
| `--students-source` | Waar de keuzelijst vandaan komt: `section` = coachingsdashboard (standaard bij `portflow_export_full.py`), `shared` = gedeelde portfolio's, `coach` = `PORTFLOW_COACH_STUDENTS_JSON` (alleen `export_single_student.py`, en daar de standaard). |
| `--section-id` | Section-ID voor `section` (standaard `72086`). |
| `--token` | Bearer token; anders uit `.env` of via een vraag. |

Je kiest een student; het script exporteert alles uit het semester (of vanaf de `start_date` van de student):

```text
exports/
  <Student Naam>/
    Semester <dd-mm-jjjj> <dd-mm-jjjj>/
      overzicht.txt                      alle gevonden items
      index.csv                          per item: map, vaardigheid, code, auteur, datum, type, niveau, bijlagen
      Evaluaties/
        Evaluatie 1 - <datum> - <titel>/  bewijsstukken, opmerkingen, zelfevaluaties, beoordelingen
        ...
      Vaardigheden/
        Vaardigheid 1 - OC - Overzicht creëren/overzicht.txt
        ...
        Vaardigheid 10 - RE - Reflecteren/overzicht.txt
      Beroepsproducten/
        ...
```

Bestanden waarnaar met een `@evidence`-vermelding in een evaluatietekst wordt verwezen, krijgen een eigen submap met het bestand en alle teksten die ernaar verwijzen. Verschil tussen de twee scripts bij *Beroepsproducten*: `portflow_export_full.py` maakt één map `Software Realiseren` met een overzicht van alle niet-vaardigheidsdoelen, `export_single_student.py` een map per doel.

### `evaluaties.py`

```bash
python3 evaluaties.py [--dump-raw]
```

Toont de evaluatieverzoeken die op jouw beoordeling wachten, met een detailmenu. Gebruikt `PORTFLOW_OWN_PORTFOLIO_ID`. `--dump-raw` schrijft de ruwe API-respons naar `evaluaties_debug.json`. Dezelfde lijst zit in `portflow.py` (meerdere studenten → evaluaties die ik nog moet beoordelen).

### `graph.py`

```bash
python3 graph.py --student <voornaam> [--token TOKEN]
```

Toont een ASCII-tijdlijn van de evaluaties van één student. `--student` mag ook een deel van de naam zijn.

## Debugbestanden

Deze bestanden komen in de map waar je het script start:

| Bestand | Aangemaakt door |
|---|---|
| `api_debug_log.jsonl` | `portflow.py --debug-api`: één JSON-regel per API-aanroep met URL, parameters, statuscode, fout en antwoord. |
| `pending_debug.json` | `portflow.py --debug-pending`: per evaluatie de beslissing om die wel of niet te tonen, met reden. |
| `schema_inventory.txt` | `portflow.py --dump-schema`: alle gevonden API-velden met type en voorbeeldwaarden. |
| `evaluaties_debug.json` | `evaluaties.py --dump-raw`. |

## Beveiliging en privacy

- `.env` bevat je token en namen van studenten; het staat in `.gitignore`. Commit het nooit.
- De debugbestanden, exports en Excel-bestanden bevatten studentgegevens. Ze staan allemaal in `.gitignore` (`exports/`, de vier debugbestanden en alle Excel-bestanden: `*.xlsx` en `*.xls`).
- Gebruik `--anoniem` als anderen meekijken.
