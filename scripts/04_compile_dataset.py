#!/usr/bin/env python3
"""Step 4: Compile a cleaned, canonical historical listing dataset."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def to_float(val: str) -> float | None:
    if val is None:
        return None
    val = str(val).strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", default="data/intermediate/extracted_listings.csv")
    parser.add_argument("--output-csv", default="data/final/historical_rentnoho_listings.csv")
    args = parser.parse_args()

    with open(args.input_csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        raise SystemExit("No extracted listings found. Run step 3 first.")

    for row in rows:
        row["monthly_rent_num"] = to_float(row.get("monthly_rent", "")) or -1
        row["sqft_num"] = to_float(row.get("sqft", "")) or -1

    rows.sort(
        key=lambda r: (
            r.get("snapshot_timestamp", ""),
            r.get("source_url", ""),
            r["monthly_rent_num"],
            r["sqft_num"],
        ),
        reverse=True,
    )

    seen = set()
    deduped = []
    for row in rows:
        key = (
            row.get("snapshot_timestamp", ""),
            row.get("source_url", ""),
            row.get("address", ""),
            row.get("listing_text", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    deduped.sort(key=lambda r: (r.get("snapshot_timestamp", ""), r.get("source_url", "")))

    out = Path(args.output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "snapshot_timestamp",
        "snapshot_date",
        "source_url",
        "snapshot_url",
        "address",
        "bedrooms",
        "bathrooms",
        "sqft",
        "monthly_rent",
        "listing_text",
    ]
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in deduped:
            writer.writerow({k: row.get(k, "") for k in fields})

    print(f"Compiled {len(deduped)} historical records")


if __name__ == "__main__":
    main()
