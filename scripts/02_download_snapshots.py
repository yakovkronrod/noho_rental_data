#!/usr/bin/env python3
"""Step 2: Download all HTML snapshots referenced in checkpoint CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen


def snapshot_url(timestamp: str, original: str) -> str:
    return f"https://web.archive.org/web/{timestamp}id_/{original}"


def safe_name(timestamp: str, original: str) -> str:
    digest = hashlib.md5(original.encode("utf-8")).hexdigest()[:10]
    return f"{timestamp}_{digest}.html"


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "noho-rental-data/1.0"})
    with urlopen(req, timeout=60) as resp:  # noqa: S310
        return resp.read()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", default="data/raw/cdx/checkpoints.csv")
    parser.add_argument("--out-dir", default="data/raw/html")
    parser.add_argument("--index-json", default="data/raw/html/index.json")
    parser.add_argument("--sleep", type=float, default=0.4)
    parser.add_argument("--max", type=int, default=None)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.input_csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if args.max:
        rows = rows[: args.max]

    index = []
    for i, row in enumerate(rows, start=1):
        ts = row["timestamp"]
        original = row["original"]
        url = snapshot_url(ts, original)
        target = out_dir / safe_name(ts, original)

        status = "ok"
        error = ""
        size = 0
        try:
            blob = fetch_bytes(url)
            target.write_bytes(blob)
            size = len(blob)
        except Exception as exc:  # noqa: BLE001
            status = "error"
            error = str(exc)

        index.append(
            {
                "timestamp": ts,
                "original": original,
                "snapshot_url": url,
                "local_file": str(target),
                "status": status,
                "error": error,
                "bytes": size,
            }
        )
        print(f"[{i}/{len(rows)}] {status:5s} {url}")
        time.sleep(args.sleep)

    with open(args.index_json, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)

    ok_count = sum(1 for item in index if item["status"] == "ok")
    print(f"Downloaded {ok_count}/{len(index)} snapshots")


if __name__ == "__main__":
    main()
