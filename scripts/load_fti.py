#!/usr/bin/env python3
"""
ThreadGrade — Fashion Transparency Index Data Loader

Loads Fashion Transparency Index (FTI) data from a manually downloaded
CSV/XLSX file and matches it against our brand list.

Download the FTI data from: https://www.fashionrevolution.org/about/transparency/
Place the file as: data/fti/fti_raw.csv or data/fti/fti_raw.xlsx

Usage:
    python scripts/load_fti.py [--force]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from thefuzz import fuzz, process
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRANDS_FILE = DATA_DIR / "brands.json"
OUTPUT_DIR = DATA_DIR / "fti"
FTI_RAW_CSV = OUTPUT_DIR / "fti_raw.csv"
FTI_RAW_XLSX = OUTPUT_DIR / "fti_raw.xlsx"

FUZZY_MATCH_THRESHOLD = 80

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("load_fti")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_brands() -> list[dict]:
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]


def load_fti_data() -> pd.DataFrame | None:
    """Load FTI raw data from CSV or XLSX."""
    if FTI_RAW_CSV.exists():
        log.info(f"Loading FTI data from {FTI_RAW_CSV}")
        return pd.read_csv(FTI_RAW_CSV)
    elif FTI_RAW_XLSX.exists():
        log.info(f"Loading FTI data from {FTI_RAW_XLSX}")
        return pd.read_excel(FTI_RAW_XLSX)
    else:
        return None


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find a column name matching one of the candidates (case-insensitive)."""
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in cols_lower:
            return cols_lower[candidate.lower()]
    # Partial match
    for candidate in candidates:
        for col_lower, col_orig in cols_lower.items():
            if candidate.lower() in col_lower:
                return col_orig
    return None


def match_brand_in_fti(brand: dict, fti_names: list[str]) -> tuple[str | None, int]:
    """Try to match a brand against FTI brand names. Returns (match, score)."""
    search_names = brand.get("search_names", [brand["name"]])
    
    best_match = None
    best_score = 0
    
    for search_name in search_names:
        result = process.extractOne(search_name, fti_names, scorer=fuzz.token_sort_ratio)
        if result and result[1] > best_score:
            best_match = result[0]
            best_score = result[1]
    
    if best_score >= FUZZY_MATCH_THRESHOLD:
        return best_match, best_score
    return None, 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Load FTI data for ThreadGrade brands")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    
    brands = load_brands()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load FTI data
    fti_df = load_fti_data()
    
    if fti_df is None:
        log.warning(
            "No FTI data file found. Download from Fashion Revolution and save as:\n"
            f"  {FTI_RAW_CSV} or {FTI_RAW_XLSX}\n"
            "Creating placeholder files for all brands."
        )
        
        for brand in tqdm(brands, desc="Creating FTI placeholders"):
            output_file = OUTPUT_DIR / f"{brand['slug']}.json"
            if output_file.exists() and not args.force:
                continue
            
            result = {
                "brand": brand["name"],
                "slug": brand["slug"],
                "data_source": "fashion_transparency_index",
                "loaded_at": datetime.now().isoformat(),
                "fti_data_available": False,
                "transparency_score": None,
                "rank": None,
                "section_scores": {},
                "note": "FTI raw data not available. Download from fashionrevolution.org",
            }
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
        
        print("\n⚠️  No FTI data file found. Placeholders created.")
        print(f"   Download FTI data and place at {FTI_RAW_CSV}")
        return
    
    log.info(f"FTI data loaded: {len(fti_df)} rows, {len(fti_df.columns)} columns")
    log.info(f"Columns: {list(fti_df.columns)}")
    
    # Identify key columns
    name_col = find_column(fti_df, ["brand", "company", "name", "brand name", "company name"])
    score_col = find_column(fti_df, ["total score", "score", "total", "overall score", "final score", "transparency score"])
    rank_col = find_column(fti_df, ["rank", "ranking", "position"])
    
    if not name_col:
        log.error("Cannot find brand/company name column in FTI data")
        log.error(f"Available columns: {list(fti_df.columns)}")
        sys.exit(1)
    
    log.info(f"Using columns: name='{name_col}', score='{score_col}', rank='{rank_col}'")
    
    # Build FTI name list
    fti_names = fti_df[name_col].dropna().astype(str).tolist()
    
    # Identify section score columns (anything with % or section-like names)
    section_cols = {}
    section_candidates = [
        "governance", "traceability", "know supply", "spotlight",
        "social", "environmental", "policy", "commitment",
        "supplier", "worker", "wages", "purchasing"
    ]
    for col in fti_df.columns:
        col_lower = col.lower()
        for candidate in section_candidates:
            if candidate in col_lower and col != name_col and col != score_col:
                section_cols[candidate] = col
                break
    
    stats = {"matched": 0, "no_match": 0, "skipped": 0}
    
    for brand in tqdm(brands, desc="Matching FTI data"):
        output_file = OUTPUT_DIR / f"{brand['slug']}.json"
        
        if output_file.exists() and not args.force:
            stats["skipped"] += 1
            continue
        
        match_name, match_score = match_brand_in_fti(brand, fti_names)
        
        if match_name:
            row = fti_df[fti_df[name_col] == match_name].iloc[0]
            
            total_score = None
            if score_col:
                try:
                    val = row[score_col]
                    total_score = round(float(val), 1) if pd.notna(val) else None
                except (ValueError, TypeError):
                    pass
            
            rank = None
            if rank_col:
                try:
                    val = row[rank_col]
                    rank = int(val) if pd.notna(val) else None
                except (ValueError, TypeError):
                    pass
            
            sections = {}
            for section_name, col in section_cols.items():
                try:
                    val = row[col]
                    sections[section_name] = round(float(val), 1) if pd.notna(val) else None
                except (ValueError, TypeError):
                    sections[section_name] = None
            
            result = {
                "brand": brand["name"],
                "slug": brand["slug"],
                "data_source": "fashion_transparency_index",
                "loaded_at": datetime.now().isoformat(),
                "fti_data_available": True,
                "fti_matched_name": match_name,
                "fti_match_score": match_score,
                "transparency_score": total_score,
                "rank": rank,
                "section_scores": sections,
            }
            stats["matched"] += 1
            log.info(f"  {brand['name']} → {match_name} (score: {total_score})")
        else:
            result = {
                "brand": brand["name"],
                "slug": brand["slug"],
                "data_source": "fashion_transparency_index",
                "loaded_at": datetime.now().isoformat(),
                "fti_data_available": False,
                "transparency_score": None,
                "rank": None,
                "section_scores": {},
            }
            stats["no_match"] += 1
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
    
    print("\n" + "=" * 60)
    print("FTI LOADER SUMMARY")
    print("=" * 60)
    print(f"  Total brands:           {len(brands)}")
    print(f"  Matched in FTI:         {stats['matched']}")
    print(f"  No FTI match:           {stats['no_match']}")
    print(f"  Skipped (cached):       {stats['skipped']}")
    print(f"  FTI dataset size:       {len(fti_df)} brands")
    print("=" * 60)


if __name__ == "__main__":
    main()
