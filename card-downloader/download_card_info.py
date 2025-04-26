#!/usr/bin/env python3
"""
download_card_info.py  –  Fetch and store Yu-Gi-Oh! card metadata
=================================================================

1. Downloads the full catalogue from YGOPRODeck (≈ 20 MB JSON).
2. Saves one compressed master file  (`cardinfo.json.zst`).
3. Optionally splits that catalogue into **one JSON per card** and
   drops each file next to its image (e.g. `ygo_cards/6983839.json`).

Dependencies
------------
pip install requests zstandard tqdm
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

try:
    import requests
    import zstandard as zstd
    from tqdm import tqdm
except ImportError as exc:  # pragma: no cover
    sys.exit(
        f"{exc.name} not installed – run:\n" "    pip install requests zstandard tqdm"
    )

API_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php"


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def fetch_catalogue() -> list[dict]:
    """Return the full list of card dictionaries from the public API."""
    print("Downloading card info …", flush=True)
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    return response.json()["data"]  # schema: list[dict]


def save_master(cards: list[dict], out_file: Path) -> None:
    """Stream-compress the entire catalogue with Zstandard level-19."""
    cctx = zstd.ZstdCompressor(level=19)

    with out_file.open("wb") as raw:  # binary sink on disk
        with cctx.stream_writer(raw) as compressor:  # still binary
            # Wrap compressor with a text interface so json.dump
            # can write str → UTF-8 → bytes transparently.
            with io.TextIOWrapper(compressor, encoding="utf-8") as text_fp:
                json.dump(cards, text_fp, separators=(",", ":"))

    size_mb = out_file.stat().st_size / 1e6
    print(f"Saved compressed catalogue: {out_file}  ({size_mb:.2f} MB)")


def split_per_card(cards: list[dict], out_dir: Path) -> None:
    """Emit one compact JSON file per card next to its image."""
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Writing per-card JSON …")

    for card in tqdm(cards, unit="card"):
        cid = str(card["id"])
        meta_path = out_dir / f"{cid}.json"
        if meta_path.exists():
            continue  # resume-safe
        meta_path.write_text(json.dumps(card, separators=(",", ":")), encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog="download_card_info",
        description="Download YGO card metadata (optionally split per card).",
    )
    parser.add_argument(
        "-d",
        "--dir",
        default="ygo_cards",
        help="image directory; used when --split is active (default: ygo_cards)",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        default="cardinfo.json.zst",
        help="destination for compressed master JSON (default: cardinfo.json.zst)",
    )
    parser.add_argument(
        "-s",
        "--split",
        action="store_true",
        help="write one JSON file per card in DIR",
    )
    args = parser.parse_args()

    cards = fetch_catalogue()
    save_master(cards, Path(args.outfile))

    if args.split:
        split_per_card(cards, Path(args.dir))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrupted by user.")
