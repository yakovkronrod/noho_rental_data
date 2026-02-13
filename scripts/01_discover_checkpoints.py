#!/usr/bin/env python3
"""Step 1: Discover all Wayback checkpoints for a target domain."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CDX_URL = "https://web.archive.org/cdx/search/cdx"


def fetch_json(url: str) -> list:
    req = Request(url, headers={"User-Agent": "noho-rental-data/1.0"})
    with urlopen(req, timeout=60) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default="rentnoho.com", help="Domain to crawl via CDX")
    parser.add_argument("--from-year", dest="from_year", default=None)
    parser.add_argument("--to-year", dest="to_year", default=None)
    parser.add_argument("--limit", type=int, default=None, help="Optional CDX result cap")
    parser.add_argument("--output-csv", default="data/raw/cdx/checkpoints.csv")
    parser.add_argument("--output-json", default="data/raw/cdx/checkpoints.json")
    args = parser.parse_args()

    params = [
        ("url", f"{args.domain}/*"),
        ("output", "json"),
        ("fl", "timestamp,original,mimetype,statuscode,digest,length"),
        ("filter", "statuscode:200"),
        ("filter", "mimetype:text/html"),
        ("collapse", "digest"),
    ]
    if args.from_year:
        params.append(("from", args.from_year))
    if args.to_year:
        params.append(("to", args.to_year))
    if args.limit:
        params.append(("limit", str(args.limit)))

    query = urlencode(params)
    payload = fetch_json(f"{CDX_URL}?{query}")
    rows = payload[1:] if payload else []

    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "original", "mimetype", "statuscode", "digest", "length"])
        writer.writerows(rows)

    out_json = Path(args.output_json)
    with out_json.open("w", encoding="utf-8") as fh:
        json.dump(
            [
                {
                    "timestamp": r[0],
                    "original": r[1],
                    "mimetype": r[2],
                    "statuscode": r[3],
                    "digest": r[4],
                    "length": r[5],
                }
                for r in rows
            ],
            fh,
            indent=2,
        )

    print(f"Discovered {len(rows)} checkpoints for {args.domain}")


if __name__ == "__main__":
    main()
