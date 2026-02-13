#!/usr/bin/env python3
"""Step 3: Parse downloaded pages and extract listing-like rental records."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path

RE_TAG = re.compile(r"<[^>]+>")
RE_SCRIPT = re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL)
RE_STYLE = re.compile(r"<style.*?>.*?</style>", re.IGNORECASE | re.DOTALL)
RE_WS = re.compile(r"\s+")

RE_MONEY = re.compile(r"\$\s?([\d,]{3,})")
RE_BED = re.compile(r"(\d+(?:\.\d+)?)\s*(?:bed|br)\b", re.IGNORECASE)
RE_BATH = re.compile(r"(\d+(?:\.\d+)?)\s*(?:bath|ba)\b", re.IGNORECASE)
RE_SQFT = re.compile(r"([\d,]{3,5})\s*(?:sq\.?\s?ft|square\s*feet|sf)\b", re.IGNORECASE)
RE_ADDRESSISH = re.compile(
    r"\b\d{1,5}\s+[\w\s\.]+\s(?:st|street|ave|avenue|rd|road|dr|drive|ln|lane|ct|court|pl|place|way|blvd|boulevard)\b",
    re.IGNORECASE,
)


def snapshot_date(ts: str) -> str:
    return datetime.strptime(ts, "%Y%m%d%H%M%S").date().isoformat()


def html_to_lines(html: str) -> list[str]:
    cleaned = RE_SCRIPT.sub(" ", html)
    cleaned = RE_STYLE.sub(" ", cleaned)
    cleaned = RE_TAG.sub("\n", cleaned)
    cleaned = unescape(cleaned)
    lines = []
    for line in cleaned.splitlines():
        line = RE_WS.sub(" ", line).strip()
        if len(line) >= 8:
            lines.append(line)
    return lines


def parse_lines(lines: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in lines:
        money = RE_MONEY.search(line)
        bed = RE_BED.search(line)
        bath = RE_BATH.search(line)
        sqft = RE_SQFT.search(line)
        addr = RE_ADDRESSISH.search(line)
        if not any([money, bed, bath, sqft]):
            continue
        rows.append(
            {
                "listing_text": line,
                "monthly_rent": money.group(1).replace(",", "") if money else "",
                "bedrooms": bed.group(1) if bed else "",
                "bathrooms": bath.group(1) if bath else "",
                "sqft": sqft.group(1).replace(",", "") if sqft else "",
                "address": addr.group(0) if addr else "",
            }
        )
    deduped = {row["listing_text"]: row for row in rows}
    return list(deduped.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-json", default="data/raw/html/index.json")
    parser.add_argument("--output-csv", default="data/intermediate/extracted_listings.csv")
    args = parser.parse_args()

    with open(args.index_json, encoding="utf-8") as fh:
        index = json.load(fh)

    all_rows: list[dict[str, str]] = []
    for item in index:
        if item.get("status") != "ok":
            continue
        html_path = Path(item["local_file"])
        if not html_path.exists():
            continue

        html = html_path.read_text(encoding="utf-8", errors="ignore")
        parsed = parse_lines(html_to_lines(html))
        for listing in parsed:
            all_rows.append(
                {
                    "snapshot_timestamp": item["timestamp"],
                    "snapshot_date": snapshot_date(item["timestamp"]),
                    "source_url": item["original"],
                    "snapshot_url": item["snapshot_url"],
                    **listing,
                }
            )

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
        writer.writerows(all_rows)

    print(f"Extracted {len(all_rows)} listing candidates")


if __name__ == "__main__":
    main()
