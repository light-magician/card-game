#!/usr/bin/env python3
"""
Download every Yu-Gi-Oh! card image from YGOPRODeck.

Usage
-----
$ python3 download_ygo_cards.py               # defaults
$ python3 download_ygo_cards.py -o pics -w 16 # custom dir & workers
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
from pathlib import Path

try:
    import requests
    from tqdm import tqdm
except ImportError as e:
    sys.exit(f"{e.name} not installed – run:  pip install requests tqdm")

API_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php"  #


def fetch_catalogue() -> list[tuple[str, str]]:
    """Return list of (card_id, image_url) for the whole catalogue."""
    print("Fetching catalogue …", flush=True)
    resp = requests.get(API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()["data"]

    pairs: dict[str, str] = {}
    for card in data:
        img = card["card_images"][0]["image_url"]  # first (usually original art)
        cid = str(card["id"])
        pairs[cid] = img  # de-dupe alt-art duplicates by id

    print(f"  ↳ {len(pairs):,} unique images discovered.")
    return list(pairs.items())


def download_one(root: Path, pair: tuple[str, str]) -> None:
    """Fetch a single image unless it already exists."""
    cid, url = pair
    dst = root / f"{cid}.jpg"
    if dst.exists():
        return

    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        dst_tmp = dst.with_suffix(".part")
        with open(dst_tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        dst_tmp.rename(dst)  # atomic replace


def main() -> None:
    p = argparse.ArgumentParser(prog="download_ygo_cards")
    p.add_argument("-o", "--out", default="ygo_cards", help="output directory")
    p.add_argument("-w", "--workers", type=int, default=8, help="parallel threads")
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    catalogue = fetch_catalogue()

    with cf.ThreadPoolExecutor(max_workers=args.workers) as exe:
        list(
            tqdm(
                exe.map(lambda pr: download_one(out_dir, pr), catalogue),
                total=len(catalogue),
                desc="Downloading",
                unit="card",
            )
        )

    print("All done ✔")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrupted.")
