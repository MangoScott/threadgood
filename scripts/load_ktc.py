#!/usr/bin/env python3
"""
ThreadGrade — KnowTheChain Benchmark Data Loader

Loads KnowTheChain benchmark data from a manually downloaded CSV/XLSX
and matches it against our brand list.

Download from: https://knowthechain.org/benchmark/
Place the file as: data/ktc/ktc_raw.csv or data/ktc/ktc_raw.xlsx

Usage:
    python scripts/load_ktc.py [--force]
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
OUTPUT_DIR = DATA_DIR / "ktc"
KTC_RAW_CSV = OUTPUT_DIR / "ktc_raw.csv"
KTC_RAW_XLSX = OUTPUT_DIR / "ktc_raw.xlsx"

FUZZY_MATCH_THRESHOLD = 80

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("load_ktc")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_brands() -> list[dict]:
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]


def load_ktc_data() -> pd.DataFrame | None:
    """Load KnowTheChain raw data from CSV or XLSX."""
    if KTC_RAW_CSV.exists():
        log.info(f"Loading KTC data from {KTC_RAW_CSV}")
        return pd.read_csv(KTC_RAW_CSV)
    elif KTC_RAW_XLSX.exists():
        log.info(f"Loading KTC data from {KTC_RAW_XLSX}")
        return pd.read_excel(KTC_RAW_XLSX)
    return None


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find a column name matching one of the candidates."""
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in cols_lower:
            return cols_lower[candidate.lower()]
    for candidate in candidates:
        for col_lower, col_orig in cols_lower.items():
            if candidate.lower() in col_lower:
                return col_orig
    return None


def match_brand_in_ktc(brand: dict, ktc_names: list[str]) -> tuple[str | None, int]:
    """Try to match a brand against KTC company names."""
    search_names = brand.get("search_names", [brand["name"]])
    
    best_match = None
    best_score = 0
    
    for name in search_names:
        result = process.extractOne(name, ktc_names, scorer=fuzz.token_sort_ratio)
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
    parser = argparse.ArgumentParser(description="Load KnowTheChain data for ThreadGrade brands")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    
    brands = load_brands()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    ktc_df = load_ktc_data()
    
    if ktc_df is None:
        log.warning(
            "No KTC data file found. Download from KnowTheChain and save as:\n"
            f"  {KTC_RAW_CSV} or {KTC_RAW_XLSX}\n"
            "Creating placeholder files."
        )
        
        for brand in tqdm(brands, desc="Creating KTC placeholders"):
            output_file = OUTPUT_DIR / f"{brand['slug']}.json"
            if output_file.exists() and not args.force:
                continue
            result = {
                "brand": brand["name"],
                "slug": brand["slug"],
                "data_source": "knowthechain",
                "loaded_at": datetime.now().isoformat(),
                "ktc_data_available": False,
                "overall_score": None,
                "theme_scores": {},
                "note": "KTC raw data not available. Download from knowthechain.org",
            }
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
        
        print("\n⚠️  No KTC data file found. Placeholders created.")
        print(f"   Download KTC data and place at {KTC_RAW_CSV}")
        return
    
    log.info(f"KTC data loaded: {len(ktc_df)} rows, {len(ktc_df.columns)} columns")
    
    # Identify columns
    name_col = find_column(ktc_df, ["company", "brand", "name", "company name"])
    score_col = find_column(ktc_df, ["total score", "overall score", "score", "total"])
    
    # Theme score columns
    theme_candidates = {
        "recruitment": ["recruitment", "hiring"],
        "worker_voice": ["worker voice", "worker engagement", "freedom of association"],
        "monitoring": ["monitoring", "auditing", "assessment"],
        "remedy": ["remedy", "remediation", "grievance"],
        "purchasing_practices": ["purchasing", "procurement"],
        "traceability": ["traceability", "supply chain", "transparency"],
        "governance": ["governance", "commitment", "policy"],
    }
    
    theme_cols = {}
    for theme_key, candidates in theme_candidates.items():
        col = find_column(ktc_df, candidates)
        if col and col != name_col and col != score_col:
            theme_cols[theme_key] = col
    
    if not name_col:
        log.error(f"Cannot find company name column. Available: {list(ktc_df.columns)}")
        sys.exit(1)
    
    log.info(f"Using: name='{name_col}', score='{score_col}', themes={list(theme_cols.keys())}")
    
    ktc_names = ktc_df[name_col].dropna().astype(str).tolist()
    
    stats = {"matched": 0, "no_match": 0, "skipped": 0}
    
    for brand in tqdm(brands, desc="Matching KTC data"):
        output_file = OUTPUT_DIR / f"{brand['slug']}.json"
        
        if output_file.exists() and not args.force:
            stats["skipped"] += 1
            continue
        
        match_name, match_score = match_brand_in_ktc(brand, ktc_names)
        
        if match_name:
            row = ktc_df[ktc_df[name_col] == match_name].iloc[0]
            
            overall = None
            if score_col:
                try:
                    val = row[score_col]
                    overall = round(float(val), 1) if pd.notna(val) else None
                except (ValueError, TypeError):
                    pass
            
            themes = {}
            for theme_key, col in theme_cols.items():
                try:
                    val = row[col]
                    themes[theme_key] = round(float(val), 1) if pd.notna(val) else None
                except (ValueError, TypeError):
                    themes[theme_key] = None
            
            result = {
                "brand": brand["name"],
                "slug": brand["slug"],
                "data_source": "knowthechain",
                "loaded_at": datetime.now().isoformat(),
                "ktc_data_available": True,
                "ktc_matched_name": match_name,
                "ktc_match_score": match_score,
                "overall_score": overall,
                "theme_scores": themes,
            }
            stats["matched"] += 1
            log.info(f"  {brand['name']} → {match_name} (score: {overall})")
        else:
            result = {
                "brand": brand["name"],
                "slug": brand["slug"],
                "data_source": "knowthechain",
                "loaded_at": datetime.now().isoformat(),
                "ktc_data_available": False,
                "overall_score": None,
                "theme_scores": {},
            }
            stats["no_match"] += 1
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
    
    print("\n" + "=" * 60)
    print("KNOWTHECHAIN LOADER SUMMARY")
    print("=" * 60)
    print(f"  Total brands:           {len(brands)}")
    print(f"  Matched in KTC:         {stats['matched']}")
    print(f"  No KTC match:           {stats['no_match']}")
    print(f"  Skipped (cached):       {stats['skipped']}")
    print(f"  KTC dataset size:       {len(ktc_df)} companies")
    print("=" * 60)


if __name__ == "__main__":
    main()
