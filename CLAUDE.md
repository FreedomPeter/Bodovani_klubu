# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A client-side SPA for calculating Czech athletics club scores from competition Excel results (MČR mládež — youth Czech championships). No build step required.

## Running the App

- Open `index.html` directly in a browser, **or**
- Use VS Code Live Server (configured on port 5501 via `.vscode/settings.json`)

## Backend Data Scraper

To refresh the clubs database:
```bash
pip install pandas playwright
playwright install chromium
python scrape.py
```
Outputs: `clubs_database.csv` and `clubs_database.json` (748 clubs from atletika.cz)

## Architecture

The entire application lives in a single file: **`index.html`** (~1450 lines). It contains all HTML, CSS, and JavaScript inline.

### Data Flow

1. User uploads `.xlsx` (competition results export)
2. SheetJS (CDN) parses the Excel file in-browser
3. JavaScript processes and ranks results per discipline
4. Points are assigned (1st=8pts, 2nd=7pts, … 8th=1pt) with tie-averaging
5. Scores are aggregated by club and region (kraj)
6. Results rendered into interactive tabs and tables

### Key Global State

```javascript
let allResults = [];        // discipline-level results
let allAthleteResults = []; // athlete-level results
let clubsDatabase = [];     // club directory (from clubs_database.json)
let KAS_MAP = {};           // club abbreviation → region mapping
```

### Points System

```javascript
const PLACE_POINTS = {1:8, 2:7, 3:6, 4:5, 5:4, 6:3, 7:2, 8:1}
```
Only top-8 placements score. Equal placements share averaged points.

### Phase Detection Logic

- `Finále` → finals
- `Finále 1` / `Finále 2` → double finals (400m), re-ranked by time across both heats
- `Rozběh` / `Běh` → preliminary heats (ranked by time)
- No phase column → direct results (field events)

### Non-scoring codes

DNS, DQ, DNF, MS, DQ*, NM, NH, PS are excluded from ranking.

### Tabs Generated

"Celkem", "Muži", "Ženy", "Kraje", "Disciplíny", "Kluby" — generated dynamically from processed data.

### Export Options

- CSV — native array serialization
- XLSX — SheetJS
- PDF — jsPDF + autoTable with embedded Inter font (`pdf-fonts.js`, `Inter-*.ttf`)

## External Dependencies (loaded via CDN)

- SheetJS: `https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js`
- Google Fonts: Inter
- jsPDF + autoTable: bundled locally (`jspdf.umd.min.js`, `jspdf.autotable.min.js`)
