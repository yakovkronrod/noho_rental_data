# noho_rental_data

Step-by-step pipeline for collecting and extracting historical rental listings from the Wayback Machine, starting with **rentnoho.com**.

## What this project does

1. **Identify all checkpoints** for `rentnoho.com` using the Internet Archive CDX API.
2. **Download all relevant archived pages** (HTML snapshots).
3. **Extract rental listing details** from each snapshot:
   - snapshot date (from timestamp)
   - source page URL
   - listing text
   - monthly rent
   - bedrooms / bathrooms
   - square feet
   - address-like text
4. **Compile one historical dataset** with deduplication and normalized numeric fields.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run step-by-step

### 1) Identify all checkpoints

```bash
python scripts/01_discover_checkpoints.py --domain rentnoho.com
```

Outputs:
- `data/raw/cdx/checkpoints.csv`
- `data/raw/cdx/checkpoints.json`

Optional debugging flags:
- `--from-year 2010 --to-year 2020`
- `--limit 500`

### 2) Download relevant files from those checkpoints

```bash
python scripts/02_download_snapshots.py
```

Outputs:
- archived HTML files in `data/raw/html/`
- index metadata file: `data/raw/html/index.json`

Optional debugging flags:
- `--max 100` (download first N only)
- `--sleep 0.8` (be gentler with requests)

### 3) Extract rental information from snapshots

```bash
python scripts/03_extract_listings.py
```

Output:
- `data/intermediate/extracted_listings.csv`

### 4) Compile a single historical listings dataset

```bash
python scripts/04_compile_dataset.py
```

Output:
- `data/final/historical_rentnoho_listings.csv`

## Notes for quality/debugging

- The extraction in step 3 uses heuristic parsing (regex + HTML text blocks), so treat output as **high-recall candidate records**.
- After first run, manually inspect `data/intermediate/extracted_listings.csv` and tighten patterns for rentnoho-specific page structure if needed.
- Because archived pages vary over time, this pipeline is intentionally modular so each step can be rerun independently.

## Next improvements (future)

- Add per-template parsers for known page types to improve precision.
- Add entity resolution to merge listings over time (same unit across snapshots).
- Extend to additional domains by changing `--domain` and parser rules.
