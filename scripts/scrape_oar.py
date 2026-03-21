#!/usr/bin/env python3
"""
ThreadGrade — Open Supply Hub (formerly OAR) Scraper

Queries the Open Supply Hub API for facility data associated with
each brand in data/brands.json.

Requires an API token — sign up free at https://opensupplyhub.org
Set OSH_API_TOKEN in your .env file.

Usage:
    python scripts/scrape_oar.py [--force] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRANDS_FILE = DATA_DIR / "brands.json"
OUTPUT_DIR = DATA_DIR / "oar"

load_dotenv(BASE_DIR / ".env")

OSH_API_BASE = "https://opensupplyhub.org/api"
OSH_API_TOKEN = os.getenv("OSH_API_TOKEN", "")

RATE_LIMIT_SECONDS = 1.2
REQUEST_TIMEOUT = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scrape_oar")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_brands() -> list[dict]:
    """Load the brand list from data/brands.json."""
    with open(BRANDS_FILE) as f:
        data = json.load(f)
    return data["brands"]


def get_session() -> requests.Session:
    """Create a requests session with auth headers."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "ThreadGrade/1.0 (FinMango 501c3 research project; contact@finmango.org)",
        "Accept": "application/json",
    })
    if OSH_API_TOKEN:
        session.headers["Authorization"] = f"Token {OSH_API_TOKEN}"
    return session


def search_facilities(query: str, session: requests.Session, page_size: int = 50) -> list[dict]:
    """
    Search OS Hub for facilities matching a query string.
    Returns a list of facility dicts.
    
    API endpoint: GET /api/facilities/?q={query}
    """
    all_facilities = []
    url = f"{OSH_API_BASE}/facilities/"
    params = {
        "q": query,
        "page_size": page_size,
        "page": 1,
    }
    
    max_pages = 5  # safety cap
    
    while params["page"] <= max_pages:
        try:
            resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            
            if resp.status_code == 401:
                log.error("Authentication failed. Check your OSH_API_TOKEN in .env")
                return []
            elif resp.status_code == 429:
                log.warning("Rate limited by OS Hub. Waiting 10 seconds...")
                time.sleep(10)
                continue
            elif resp.status_code != 200:
                log.warning(f"OS Hub API returned {resp.status_code} for '{query}'")
                break
            
            data = resp.json()
            
            # Handle paginated response
            if isinstance(data, dict):
                features = data.get("features", [])
                if not features:
                    # Maybe it's a flat results list
                    results = data.get("results", [])
                    if results:
                        all_facilities.extend(results)
                    break
                
                all_facilities.extend(features)
                
                # Check for next page
                next_url = data.get("next")
                if not next_url:
                    break
                params["page"] += 1
            elif isinstance(data, list):
                all_facilities.extend(data)
                break
            else:
                break
            
            time.sleep(RATE_LIMIT_SECONDS)
            
        except requests.RequestException as e:
            log.warning(f"Request failed for '{query}': {e}")
            break
    
    return all_facilities


def parse_facility(raw: dict) -> dict:
    """
    Parse a raw OS Hub facility record into our schema.
    OS Hub uses GeoJSON-like format with properties nested inside.
    """
    # Handle GeoJSON feature format
    if "properties" in raw:
        props = raw["properties"]
        geometry = raw.get("geometry", {})
    else:
        props = raw
        geometry = {}
    
    facility = {
        "os_id": props.get("os_id", props.get("id", "")),
        "name": props.get("name", ""),
        "address": props.get("address", ""),
        "country_code": props.get("country_code", ""),
        "country_name": props.get("country_name", ""),
        "lat": None,
        "lng": None,
    }
    
    # Extract coordinates from geometry
    coords = geometry.get("coordinates", [])
    if coords and len(coords) >= 2:
        facility["lng"] = coords[0]
        facility["lat"] = coords[1]
    
    # Additional fields if available
    if "number_of_workers" in props:
        facility["number_of_workers"] = props["number_of_workers"]
    if "facility_type" in props:
        facility["facility_type"] = props["facility_type"]
    if "processing_type" in props:
        facility["processing_type"] = props["processing_type"]
    if "product_type" in props:
        facility["product_type"] = props["product_type"]
    if "sector" in props:
        facility["sector"] = props["sector"]
    
    # Contributors (brands connected to this facility)
    contributors = props.get("contributors", [])
    if contributors:
        facility["connected_brands"] = []
        for c in contributors:
            if isinstance(c, dict):
                facility["connected_brands"].append(c.get("name", str(c.get("id", ""))))
            elif isinstance(c, str):
                facility["connected_brands"].append(c)
    
    return facility


def summarize_facilities(facilities: list[dict]) -> dict:
    """Create summary statistics from parsed facilities."""
    if not facilities:
        return {
            "facility_count": 0,
            "countries": [],
            "country_count": 0,
            "facilities": [],
        }
    
    countries = {}
    for f in facilities:
        cc = f.get("country_code", "")
        cn = f.get("country_name", cc)
        if cc:
            countries[cc] = cn
    
    return {
        "facility_count": len(facilities),
        "countries": sorted([
            {"code": code, "name": name}
            for code, name in countries.items()
        ], key=lambda x: x["name"]),
        "country_count": len(countries),
        "facilities": [
            {
                "os_id": f.get("os_id", ""),
                "name": f.get("name", ""),
                "address": f.get("address", ""),
                "country_code": f.get("country_code", ""),
                "country_name": f.get("country_name", ""),
            }
            for f in facilities[:100]  # cap detail at 100 facilities
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def scrape_brand(brand: dict, session: requests.Session) -> dict:
    """Scrape Open Supply Hub data for a single brand."""
    search_names = brand.get("search_names", [brand["name"]])
    all_facilities = {}  # de-dupe by OS ID
    searched_terms = []
    
    # Search with brand name (primary) and sometimes parent
    search_terms = [brand["name"]]
    parent = brand.get("parent", "")
    if parent and parent != brand["name"]:
        search_terms.append(parent)
    
    for term in search_terms:
        time.sleep(RATE_LIMIT_SECONDS)
        
        log.debug(f"  Searching OS Hub: '{term}'")
        searched_terms.append(term)
        
        raw_facilities = search_facilities(term, session)
        
        for raw in raw_facilities:
            parsed = parse_facility(raw)
            os_id = parsed.get("os_id", "")
            if os_id and os_id not in all_facilities:
                all_facilities[os_id] = parsed
        
        if raw_facilities:
            log.info(f"  Found {len(raw_facilities)} facility/ies for '{term}'")
    
    facilities = list(all_facilities.values())
    summary = summarize_facilities(facilities)
    
    return {
        "brand": brand["name"],
        "slug": brand["slug"],
        "parent": brand.get("parent", ""),
        "search_terms_used": searched_terms,
        "data_source": "open_supply_hub",
        "scraped_at": datetime.now().isoformat(),
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Scrape Open Supply Hub facility data for ThreadGrade brands")
    parser.add_argument("--force", action="store_true", help="Re-scrape even if cached data exists")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of brands to process (0 = all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check API token
    if not OSH_API_TOKEN:
        log.error(
            "OSH_API_TOKEN not set. Sign up at https://opensupplyhub.org and "
            "generate a token at My Account > Settings > API. "
            "Add it to your .env file."
        )
        print("\n⚠️  No OS Hub API token found. Creating placeholder data files.")
        print("   Set OSH_API_TOKEN in .env to get real facility data.\n")
    
    # Load brands
    if not BRANDS_FILE.exists():
        log.error(f"Brand list not found at {BRANDS_FILE}")
        sys.exit(1)
    
    brands = load_brands()
    if args.limit > 0:
        brands = brands[:args.limit]
    
    log.info(f"Processing {len(brands)} brands")
    
    # Ensure output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Stats
    stats = {
        "processed": 0,
        "with_data": 0,
        "no_results": 0,
        "skipped_cached": 0,
        "errors": 0,
        "total_facilities": 0,
    }
    
    session = get_session()
    
    for brand in tqdm(brands, desc="Scraping OS Hub data"):
        slug = brand["slug"]
        output_file = OUTPUT_DIR / f"{slug}.json"
        
        # Skip if cached (unless --force)
        if output_file.exists() and not args.force:
            stats["skipped_cached"] += 1
            log.debug(f"Skipping {brand['name']} (cached)")
            continue
        
        try:
            if not OSH_API_TOKEN:
                # Create placeholder with no data
                result = {
                    "brand": brand["name"],
                    "slug": slug,
                    "parent": brand.get("parent", ""),
                    "search_terms_used": [],
                    "data_source": "open_supply_hub",
                    "scraped_at": datetime.now().isoformat(),
                    "summary": summarize_facilities([]),
                    "note": "No OSH_API_TOKEN configured. Set token in .env to fetch real data.",
                }
            else:
                result = scrape_brand(brand, session)
            
            # Save result
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2, default=str)
            
            stats["processed"] += 1
            facility_count = result["summary"]["facility_count"]
            stats["total_facilities"] += facility_count
            
            if facility_count > 0:
                stats["with_data"] += 1
                log.info(
                    f"{brand['name']}: {facility_count} facilities "
                    f"across {result['summary']['country_count']} countries"
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
                "summary": summarize_facilities([]),
            }
            with open(output_file, "w") as f:
                json.dump(error_result, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "=" * 60)
    print("OPEN SUPPLY HUB SCRAPER SUMMARY")
    print("=" * 60)
    print(f"  Total brands:           {len(brands)}")
    print(f"  Processed:              {stats['processed']}")
    print(f"  Skipped (cached):       {stats['skipped_cached']}")
    print(f"  With facility data:     {stats['with_data']}")
    print(f"  No results found:       {stats['no_results']}")
    print(f"  Total facilities:       {stats['total_facilities']}")
    print(f"  Errors:                 {stats['errors']}")
    print(f"  Output dir:             {OUTPUT_DIR}")
    if not OSH_API_TOKEN:
        print(f"  ⚠️  API TOKEN MISSING — all results are placeholders")
    print("=" * 60)


if __name__ == "__main__":
    main()
