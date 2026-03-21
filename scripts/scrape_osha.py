#!/usr/bin/env python3
"""
ThreadGrade — OSHA Enforcement Data Scraper

Queries the DOL Data Portal V4 API for OSHA inspections and violations
for each brand in data/brands.json.

Strategy: The DOL V4 API does not support server-side text search.
We batch-download OSHA inspection records and filter them locally
by establishment name using fuzzy matching.

API docs: https://dataportal.dol.gov
Register for a free API key at: https://dataportal.dol.gov/registration
Set DOL_API_KEY in your .env file.

Usage:
    python scripts/scrape_osha.py [--force] [--limit N] [--verbose]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv
from thefuzz import fuzz
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRANDS_FILE = DATA_DIR / "brands.json"
OUTPUT_DIR = DATA_DIR / "osha"
CACHE_FILE = DATA_DIR / "osha" / "_inspection_cache.json"

load_dotenv(BASE_DIR / ".env")

DOL_API_KEY = os.getenv("DOL_API_KEY", "")

# DOL Data Portal V4 API
DOL_API_BASE = "https://apiprod.dol.gov/v4/get/OSHA"

# OSHA-relevant SIC code ranges
APPAREL_SIC_RANGES = [
    (2300, 2399),  # Apparel manufacturing
    (5600, 5699),  # Apparel retail
    (5311, 5311),  # Department stores
    (4225, 4225),  # Warehousing
    (5944, 5949),  # Misc retail
]

RATE_LIMIT_SECONDS = 2.0  # DOL API has aggressive rate limiting
FUZZY_MATCH_THRESHOLD = 80
REQUEST_TIMEOUT = 30
BATCH_SIZE = 500  # Records per API page (smaller = friendlier to rate limits)
MAX_RETRIES = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scrape_osha")


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_brands():
    """Load the brand list from data/brands.json."""
    with open(BRANDS_FILE) as f:
        data = json.load(f)
    return data["brands"]


def download_osha_inspections(session):
    """
    Download all OSHA inspection records from the DOL V4 API.
    Caches to disk since this dataset is large.
    Returns list of inspection dicts.
    """
    # Check cache first
    if CACHE_FILE.exists():
        cache_age = time.time() - CACHE_FILE.stat().st_mtime
        if cache_age < 86400 * 7:  # refresh weekly
            log.info(f"Loading cached OSHA data ({CACHE_FILE.stat().st_size / 1024 / 1024:.1f} MB)")
            with open(CACHE_FILE) as f:
                return json.load(f)
            
    if not DOL_API_KEY:
        log.warning("No DOL_API_KEY — cannot download bulk inspection data")
        return []

    log.info("Downloading OSHA inspection records from DOL API (this may take a few minutes)...")
    
    all_records = []
    offset = 0
    rate_limit_retries = 0
    
    while True:
        params = {
            "X-API-KEY": DOL_API_KEY,
            "limit": str(BATCH_SIZE),
            "offset": str(offset),
        }
        
        try:
            resp = session.get(
                f"{DOL_API_BASE}/inspection/json",
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            
            if resp.status_code == 401 or resp.status_code == 403:
                log.error(f"API auth failed ({resp.status_code}). Check DOL_API_KEY in .env")
                break
            elif resp.status_code == 429:
                rate_limit_retries += 1
                if rate_limit_retries > MAX_RETRIES:
                    log.error(f"Rate limited {MAX_RETRIES} times. Try again later.")
                    break
                wait_time = 10 * (2 ** (rate_limit_retries - 1))  # 10, 20, 40, 80, 160s
                log.warning(f"Rate limited (attempt {rate_limit_retries}/{MAX_RETRIES}). Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            elif resp.status_code != 200:
                log.warning(f"DOL API returned {resp.status_code}: {resp.text[:200]}")
                break
            
            data = resp.json()
            records = data.get("data", [])
            
            if not records:
                break
            
            all_records.extend(records)
            offset += BATCH_SIZE
            
            log.info(f"  Downloaded {len(all_records):,} inspection records so far...")
            time.sleep(RATE_LIMIT_SECONDS)
            
            # Safety cap — OSHA has ~500K+ records. For MVP, get first 50K.
            if len(all_records) >= 50000:
                log.info(f"  Reached 50K record cap. Use bulk CSV for full dataset.")
                break
                
        except requests.RequestException as e:
            log.error(f"API request failed: {e}")
            break
    
    log.info(f"Downloaded {len(all_records):,} total OSHA inspection records")
    
    # Cache to disk
    if all_records:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(all_records, f)
        log.info(f"Cached to {CACHE_FILE}")
    
    return all_records


# ---------------------------------------------------------------------------
# Matching & Filtering
# ---------------------------------------------------------------------------

def is_relevant_sic(sic_code):
    """Check if SIC code falls within apparel/retail/warehouse ranges."""
    if sic_code is None:
        return True
    try:
        sic = int(str(sic_code).strip())
    except (ValueError, TypeError):
        return True
    for lo, hi in APPAREL_SIC_RANGES:
        if lo <= sic <= hi:
            return True
    return False


def fuzzy_match(name, candidates, threshold=FUZZY_MATCH_THRESHOLD):
    """Check if `name` fuzzy-matches any of the `candidates`."""
    name_lower = name.lower().strip()
    for candidate in candidates:
        candidate_lower = candidate.lower().strip()
        if candidate_lower in name_lower or name_lower in candidate_lower:
            return True
        if fuzz.ratio(name_lower, candidate_lower) >= threshold:
            return True
        if fuzz.partial_ratio(name_lower, candidate_lower) >= threshold + 5:
            return True
    return False


def find_brand_inspections(brand, all_inspections):
    """
    Filter the full inspection dataset for records matching a brand.
    Uses fuzzy matching on establishment name against brand search_names.
    """
    search_names = brand.get("search_names", [brand["name"]])
    matches = []
    
    for record in all_inspections:
        estab_name = record.get("estab_name", "")
        if not estab_name:
            continue
        
        if fuzzy_match(estab_name, search_names):
            matches.append(record)
    
    return matches


def _safe_int(val):
    if val is None:
        return 0
    try:
        return int(float(str(val).replace(",", "")))
    except (ValueError, TypeError):
        return 0


def _safe_float(val):
    if val is None:
        return 0.0
    try:
        return float(str(val).replace(",", "").replace("$", ""))
    except (ValueError, TypeError):
        return 0.0


def parse_date(d):
    """Try to parse various date formats."""
    if not d or not isinstance(d, str):
        return None
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y%m%d"]:
        try:
            return datetime.strptime(d[:10], fmt[:8] if len(d) < 11 else fmt)
        except ValueError:
            continue
    return None


def build_inspections(raw_records):
    """Normalize raw API records."""
    inspections = []
    for r in raw_records:
        inspections.append({
            "activity_nr": str(r.get("activity_nr", "")),
            "estab_name": r.get("estab_name", ""),
            "site_address": r.get("site_address", ""),
            "site_city": r.get("site_city", ""),
            "site_state": r.get("site_state", ""),
            "site_zip": r.get("site_zip", ""),
            "sic_code": r.get("sic_code", ""),
            "naics_code": r.get("naics_code", ""),
            "open_date": r.get("open_date", ""),
            "close_case_date": r.get("close_case_date", ""),
            "insp_type": r.get("insp_type", ""),
        })
    return inspections


def download_violations_for(activity_nrs, session):
    """Download violation records for specific inspection activity numbers."""
    if not DOL_API_KEY or not activity_nrs:
        return []
    
    all_violations = []
    offset = 0
    
    while True:
        params = {
            "X-API-KEY": DOL_API_KEY,
            "limit": str(BATCH_SIZE),
            "offset": str(offset),
        }
        
        try:
            resp = session.get(
                f"{DOL_API_BASE}/violation/json",
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            
            if resp.status_code != 200:
                break
            
            data = resp.json()
            records = data.get("data", [])
            if not records:
                break
            
            # Filter to matching activity numbers
            matching = [r for r in records if str(r.get("activity_nr", "")) in activity_nrs]
            all_violations.extend(matching)
            
            offset += BATCH_SIZE
            time.sleep(RATE_LIMIT_SECONDS)
            
            # Cap at 10K violation records
            if offset >= 10000:
                break
                
        except requests.RequestException:
            break
    
    return all_violations


def summarize_inspections(inspections, violations=None):
    """Create a summary from parsed inspections and violations."""
    if not inspections:
        return {
            "total_inspections": 0,
            "serious_violations": 0,
            "willful_violations": 0,
            "repeat_violations": 0,
            "other_violations": 0,
            "total_penalties": 0.0,
            "most_recent_inspection": None,
            "recent_serious_violations_3yr": 0,
            "recent_willful_violations_3yr": 0,
            "establishments_found": [],
            "states": [],
        }
    
    # Count violations from violation records if available
    total_serious = 0
    total_willful = 0
    total_repeat = 0
    total_other = 0
    total_penalties = 0.0
    
    if violations:
        for v in violations:
            viol_type = str(v.get("viol_type", "")).upper()
            penalty = _safe_float(v.get("current_penalty", 0))
            total_penalties += penalty
            
            if viol_type == "S":
                total_serious += 1
            elif viol_type == "W":
                total_willful += 1
            elif viol_type == "R":
                total_repeat += 1
            else:
                total_other += 1
    
    # Find most recent inspection date
    dates = [parse_date(i.get("open_date")) for i in inspections]
    dates = [d for d in dates if d]
    most_recent = max(dates).strftime("%Y-%m-%d") if dates else None
    
    # Recent violations (past 3 years)
    three_years_ago = datetime.now() - timedelta(days=3 * 365)
    recent_serious = 0
    recent_willful = 0
    
    if violations:
        for v in violations:
            # Match violation to its inspection date
            act_nr = str(v.get("activity_nr", ""))
            for insp in inspections:
                if str(insp.get("activity_nr", "")) == act_nr:
                    d = parse_date(insp.get("open_date"))
                    if d and d >= three_years_ago:
                        viol_type = str(v.get("viol_type", "")).upper()
                        if viol_type == "S":
                            recent_serious += 1
                        elif viol_type == "W":
                            recent_willful += 1
                    break
    
    estab_names = list(set(
        i.get("estab_name", "") for i in inspections if i.get("estab_name")
    ))[:20]
    
    states = sorted(set(
        i.get("site_state", "") for i in inspections if i.get("site_state")
    ))
    
    return {
        "total_inspections": len(inspections),
        "serious_violations": total_serious,
        "willful_violations": total_willful,
        "repeat_violations": total_repeat,
        "other_violations": total_other,
        "total_penalties": round(total_penalties, 2),
        "most_recent_inspection": most_recent,
        "recent_serious_violations_3yr": recent_serious,
        "recent_willful_violations_3yr": recent_willful,
        "establishments_found": estab_names,
        "states": states,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Scrape OSHA enforcement data for ThreadGrade brands")
    parser.add_argument("--force", action="store_true", help="Re-scrape even if cached data exists")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of brands to process (0 = all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--refresh-cache", action="store_true", help="Force re-download of OSHA inspection data")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check API key
    if not DOL_API_KEY:
        log.error(
            "DOL_API_KEY not set. Register free at https://dataportal.dol.gov/registration\n"
            "  Add DOL_API_KEY to your .env file."
        )
        sys.exit(1)
    
    # Load brands
    if not BRANDS_FILE.exists():
        log.error(f"Brand list not found at {BRANDS_FILE}")
        sys.exit(1)
    
    brands = load_brands()
    if args.limit > 0:
        brands = brands[:args.limit]
    
    log.info(f"Processing {len(brands)} brands")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clear cache if requested
    if args.refresh_cache and CACHE_FILE.exists():
        CACHE_FILE.unlink()
    
    # Step 1: Download/load bulk OSHA inspection data
    session = requests.Session()
    session.headers.update({
        "User-Agent": "ThreadGrade/1.0 (FinMango 501c3 research project; contact@finmango.org)",
        "Accept": "application/json",
    })
    
    all_inspections = download_osha_inspections(session)
    
    if not all_inspections:
        log.error("No OSHA inspection data available. Check your API key.")
        sys.exit(1)
    
    log.info(f"Searching {len(all_inspections):,} inspection records for {len(brands)} brands...")
    
    # Step 2: Match each brand against the inspection data
    stats = {
        "processed": 0,
        "with_data": 0,
        "with_violations": 0,
        "no_results": 0,
        "skipped_cached": 0,
        "errors": 0,
    }
    
    for brand in tqdm(brands, desc="Matching OSHA data"):
        slug = brand["slug"]
        output_file = OUTPUT_DIR / f"{slug}.json"
        
        if output_file.exists() and not args.force:
            stats["skipped_cached"] += 1
            continue
        
        try:
            # Find matching inspections
            matched_inspections = find_brand_inspections(brand, all_inspections)
            inspections = build_inspections(matched_inspections)
            
            summary = summarize_inspections(inspections)
            
            result = {
                "brand": brand["name"],
                "slug": slug,
                "parent": brand.get("parent", ""),
                "search_terms_used": brand.get("search_names", [brand["name"]]),
                "data_source": "dol_data_portal_v4",
                "scraped_at": datetime.now().isoformat(),
                "summary": summary,
                "inspections": inspections[:50],
                "raw_match_count": len(matched_inspections),
            }
            
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2, default=str)
            
            stats["processed"] += 1
            
            if len(inspections) > 0:
                stats["with_data"] += 1
                log.info(
                    f"{brand['name']}: {len(inspections)} inspections, "
                    f"{summary['serious_violations']} serious violations, "
                    f"${summary['total_penalties']:,.2f} penalties"
                )
            else:
                stats["no_results"] += 1
            
        except Exception as e:
            stats["errors"] += 1
            log.error(f"Error processing {brand['name']}: {e}")
            
            error_result = {
                "brand": brand["name"],
                "slug": slug,
                "error": str(e),
                "scraped_at": datetime.now().isoformat(),
                "summary": summarize_inspections([]),
                "inspections": [],
            }
            with open(output_file, "w") as f:
                json.dump(error_result, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "=" * 60)
    print("OSHA SCRAPER SUMMARY")
    print("=" * 60)
    print(f"  Total brands:           {len(brands)}")
    print(f"  Inspection records:     {len(all_inspections):,}")
    print(f"  Processed:              {stats['processed']}")
    print(f"  Skipped (cached):       {stats['skipped_cached']}")
    print(f"  With OSHA data:         {stats['with_data']}")
    print(f"  No results found:       {stats['no_results']}")
    print(f"  Errors:                 {stats['errors']}")
    print(f"  Output dir:             {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
