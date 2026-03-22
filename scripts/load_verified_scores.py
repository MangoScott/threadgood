#!/usr/bin/env python3
"""
ThreadGrade — Verified Public Scores Loader

Writes FTI and KnowTheChain data files using ONLY real, publicly published
scores from official sources. Every score includes its source citation.

Sources:
  - Fashion Transparency Index 2023 & 2024 by Fashion Revolution
    https://www.fashionrevolution.org/fashion-transparency-index/
    Open data: https://wikirate.org/Fashion_Transparency_Index
  - KnowTheChain 2023 Apparel & Footwear Benchmark
    https://knowthechain.org/benchmark/
    https://www.business-humanrights.org/en/from-us/briefings/2023-knowthechain-apparel-footwear-benchmark/

Brands without verified scores get fti_data_available=false / ktc_data_available=false.
No data is fabricated — if we can't cite a public source, we don't include it.

Usage:
    python scripts/load_verified_scores.py [--force]
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FTI_DIR = DATA_DIR / "fti"
KTC_DIR = DATA_DIR / "ktc"
BRANDS_FILE = DATA_DIR / "brands.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("verified_scores")


# ============================================================================
# VERIFIED FTI SCORES
# All scores below are from Fashion Revolution's published reports.
# ============================================================================

FTI_SCORES = {
    # ---- FTI 2023 (main edition, 250 brands) ----
    # Source: Fashion Transparency Index 2023, Fashion Revolution
    # https://www.fashionrevolution.org/fashion-transparency-index-2023/
    # Confirmed via press releases, media coverage, and Wikirate open data

    "hm": {
        "score": 71, "edition": "2023",
        "source": "Fashion Transparency Index 2023, Fashion Revolution",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index-2023/",
        "context": "Among the highest-scoring mainstream brands; scored 71% in main transparency assessment of 250 brands.",
    },
    "the-north-face": {
        "score": 66, "edition": "2023",
        "source": "Fashion Transparency Index 2023, Fashion Revolution (VF Corporation brands)",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index-2023/",
        "context": "Scored 66% as part of VF Corporation's brand portfolio.",
    },
    "timberland": {
        "score": 66, "edition": "2023",
        "source": "Fashion Transparency Index 2023, Fashion Revolution (VF Corporation brands)",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index-2023/",
        "context": "Scored 66% as part of VF Corporation's brand portfolio.",
    },
    "zara": {
        "score": 50, "edition": "2023",
        "source": "Fashion Transparency Index 2023, Fashion Revolution (Inditex)",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index-2023/",
        "context": "Part of Inditex group; scored 50% on supply chain transparency.",
    },
    "shein": {
        "score": 7, "edition": "2023",
        "source": "Fashion Transparency Index 2023, Fashion Revolution",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index-2023/",
        "context": "Scored 7%, among the lowest-scoring brands in the index.",
    },

    # ---- FTI 2024 "What Fuels Fashion" special edition ----
    # Source: Fashion Transparency Index 2024, Fashion Revolution
    # https://www.fashionrevolution.org/fashion-transparency-index/
    # This edition focused specifically on climate & energy transparency

    "puma": {
        "score": 75, "edition": "2024 (What Fuels Fashion)",
        "source": "Fashion Transparency Index 2024 What Fuels Fashion, Fashion Revolution",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index/",
        "context": "Highest scoring brand (75%) in the 2024 climate-focused transparency edition.",
    },
    "champion": {
        "score": 58, "edition": "2024 (What Fuels Fashion)",
        "source": "Fashion Transparency Index 2024 What Fuels Fashion, Fashion Revolution",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index/",
        "context": "Scored 58% on climate/energy transparency (Hanesbrands portfolio).",
    },
    "hanes": {
        "score": 58, "edition": "2024 (What Fuels Fashion)",
        "source": "Fashion Transparency Index 2024 What Fuels Fashion, Fashion Revolution",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index/",
        "context": "Scored 58% on climate/energy transparency (Hanesbrands portfolio).",
    },
    "adidas": {
        "score": 49, "edition": "2024 (What Fuels Fashion)",
        "source": "Fashion Transparency Index 2024 What Fuels Fashion, Fashion Revolution",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index/",
        "context": "Scored 49% on climate/energy transparency in the 2024 special edition.",
    },
    "lululemon": {
        "score": 50, "edition": "2024 (What Fuels Fashion)",
        "source": "Fashion Transparency Index 2024 What Fuels Fashion, Fashion Revolution",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index/",
        "context": "Scored 50% on climate/energy transparency.",
    },
    "fashion-nova": {
        "score": 0, "edition": "2024 (What Fuels Fashion)",
        "source": "Fashion Transparency Index 2024 What Fuels Fashion, Fashion Revolution",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index/",
        "context": "Scored 0% — zero climate/energy transparency disclosures.",
    },
    "forever-21": {
        "score": 0, "edition": "2024 (What Fuels Fashion)",
        "source": "Fashion Transparency Index 2024 What Fuels Fashion, Fashion Revolution",
        "source_url": "https://www.fashionrevolution.org/fashion-transparency-index/",
        "context": "Scored 0% — zero climate/energy transparency disclosures.",
    },
}


# ============================================================================
# VERIFIED KNOWTHECHAIN SCORES
# All scores from KnowTheChain 2023 Apparel & Footwear Benchmark.
# Source: https://knowthechain.org/benchmark/
# Confirmed via CNBC, IHRB, Business & Human Rights Resource Centre
# ============================================================================

KTC_SCORES = {
    "lululemon": {
        "score": 63, "rank": 1, "total_companies": 65,
        "source": "KnowTheChain 2023 Apparel & Footwear Benchmark",
        "source_url": "https://knowthechain.org/benchmark/",
        "context": "Highest scoring company (63/100) in the 2023 benchmark of 65 companies. Commended for 'markedly stronger human rights due diligence.'",
    },
    "puma": {
        "score": 58, "rank": 2, "total_companies": 65,
        "source": "KnowTheChain 2023 Apparel & Footwear Benchmark",
        "source_url": "https://knowthechain.org/benchmark/",
        "context": "Second highest scorer (58/100). One of only 3 companies scoring above 50.",
    },
    "adidas": {
        "score": 55, "rank": 3, "total_companies": 65,
        "source": "KnowTheChain 2023 Apparel & Footwear Benchmark",
        "source_url": "https://knowthechain.org/benchmark/",
        "context": "Third highest scorer (55/100). One of only 3 companies scoring above 50.",
    },
    "nike": {
        "score": 48, "rank": 6, "total_companies": 65,
        "source": "KnowTheChain 2023 Apparel & Footwear Benchmark",
        "source_url": "https://knowthechain.org/benchmark/",
        "context": "Ranked 6th (48/100). Above average but did not reach the 50-point threshold.",
    },
}

# Industry context for KTC (applies to all brands in the benchmark)
KTC_INDUSTRY_CONTEXT = {
    "benchmark_year": 2023,
    "total_companies_assessed": 65,
    "industry_average": 21,
    "highest_score": 63,
    "companies_above_50": 3,
    "companies_at_5_or_below": "over 20%",
    "worst_theme_scores": {
        "purchasing_practices": 12,
        "remedy": 7,
        "recruitment": 14,
    },
}


def write_fti_files(brands: list[dict], force: bool = False):
    """Write FTI data files for all brands."""
    FTI_DIR.mkdir(parents=True, exist_ok=True)
    count = 0

    for brand in brands:
        slug = brand["slug"]
        out_path = FTI_DIR / f"{slug}.json"

        if out_path.exists() and not force:
            continue

        fti_info = FTI_SCORES.get(slug)

        data = {
            "brand": brand["name"],
            "slug": slug,
            "data_source": "fashion_transparency_index",
            "loaded_at": datetime.now().isoformat(),
            "fti_data_available": fti_info is not None,
        }

        if fti_info:
            data["transparency_score"] = fti_info["score"]
            data["edition"] = fti_info["edition"]
            data["source"] = fti_info["source"]
            data["source_url"] = fti_info["source_url"]
            data["context"] = fti_info["context"]
            data["rank"] = None  # Exact rank not available from summaries
            data["section_scores"] = {}
            count += 1
        else:
            data["transparency_score"] = None
            data["rank"] = None
            data["section_scores"] = {}

        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)

    return count


def write_ktc_files(brands: list[dict], force: bool = False):
    """Write KTC data files for all brands."""
    KTC_DIR.mkdir(parents=True, exist_ok=True)
    count = 0

    for brand in brands:
        slug = brand["slug"]
        out_path = KTC_DIR / f"{slug}.json"

        if out_path.exists() and not force:
            continue

        ktc_info = KTC_SCORES.get(slug)

        data = {
            "brand": brand["name"],
            "slug": slug,
            "data_source": "knowthechain",
            "loaded_at": datetime.now().isoformat(),
            "ktc_data_available": ktc_info is not None,
        }

        if ktc_info:
            data["overall_score"] = ktc_info["score"]
            data["rank"] = ktc_info["rank"]
            data["total_companies"] = ktc_info["total_companies"]
            data["source"] = ktc_info["source"]
            data["source_url"] = ktc_info["source_url"]
            data["context"] = ktc_info["context"]
            data["industry_context"] = KTC_INDUSTRY_CONTEXT
            data["theme_scores"] = {}  # Detailed theme scores not in public summaries
            count += 1
        else:
            data["overall_score"] = None
            data["theme_scores"] = {}

        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)

    return count


def main():
    parser = argparse.ArgumentParser(description="Load verified public scores")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    with open(BRANDS_FILE) as f:
        brands = json.load(f)["brands"]

    fti_count = write_fti_files(brands, args.force)
    ktc_count = write_ktc_files(brands, args.force)

    print("\n" + "=" * 60)
    print("VERIFIED SCORES LOADER SUMMARY")
    print("=" * 60)
    print(f"  Total brands:          {len(brands)}")
    print(f"  FTI scores written:    {fti_count} / {len(brands)}")
    print(f"  KTC scores written:    {ktc_count} / {len(brands)}")
    print(f"")
    print(f"  FTI brands with data:  {len(FTI_SCORES)}")
    print(f"  KTC brands with data:  {len(KTC_SCORES)}")
    print(f"")
    print(f"  All scores are from published public sources.")
    print(f"  Brands without verified scores have data_available=false.")
    print("=" * 60)


if __name__ == "__main__":
    main()
