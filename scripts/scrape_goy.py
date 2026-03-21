#!/usr/bin/env python3
"""
ThreadGrade — Good On You Ratings Scraper

Scrapes publicly available brand ratings from Good On You's directory.
This provides a trusted third-party cross-reference for validation.

Good On You rates brands on a 1-5 scale across:
  - People (labor rights)
  - Planet (environmental impact)
  - Animals (animal welfare)

Usage:
    python scripts/scrape_goy.py [--force] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRANDS_FILE = DATA_DIR / "brands.json"
OUTPUT_DIR = DATA_DIR / "goy"

GOY_BASE = "https://directory.goodonyou.eco"
RATE_LIMIT_SECONDS = 2.0
REQUEST_TIMEOUT = 15

# Mapping of ThreadGrade brand slugs to Good On You URL slugs
# (some brands may have different URL patterns)
GOY_SLUG_OVERRIDES = {
    "target-all-in-motion": "target",
    "target-goodfellow": "target",
    "target-a-new-day": "target",
    "walmart-george": "walmart",
    "walmart-time-and-tru": "walmart",
    "walmart-wonder-nation": "walmart",
    "costco-kirkland": "costco",
    "the-north-face": "the-north-face",
    "levis": "levis",
    "hm": "h-m",
    "tj-maxx": "tj-maxx",
    "abercrombie-fitch": "abercrombie-fitch",
    "prettylittlething": "prettylittlething",
    "amazon-essentials": "amazon-fashion",
    "fashion-nova": "fashion-nova",
    "old-navy": "old-navy",
    "banana-republic": "banana-republic",
    "victoria-secret": "victorias-secret",
    "american-eagle": "american-eagle-outfitters",
    "free-people": "free-people",
    "urban-outfitters": "urban-outfitters",
    "eileen-fisher": "eileen-fisher",
    "fruit-of-the-loom": "fruit-of-the-loom",
    "brooks-brothers": "brooks-brothers",
    "columbia-sportswear": "columbia-sportswear",
    "under-armour": "under-armour",
    "new-balance": "new-balance",
    "ralph-lauren": "ralph-lauren",
    "tommy-hilfiger": "tommy-hilfiger",
    "calvin-klein": "calvin-klein",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scrape_goy")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_brands():
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]


def get_goy_slug(brand):
    """Get the Good On You URL slug for a brand."""
    slug = brand["slug"]
    if slug in GOY_SLUG_OVERRIDES:
        return GOY_SLUG_OVERRIDES[slug]
    return slug


def scrape_brand_rating(goy_slug, session):
    """
    Scrape a brand page from Good On You directory.
    Returns parsed rating data or None if not found.
    """
    url = f"{GOY_BASE}/brand/{goy_slug}"
    
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        
        if resp.status_code == 404:
            return None
        elif resp.status_code != 200:
            log.debug(f"GOY returned {resp.status_code} for {goy_slug}")
            return None
        
        html = resp.text
        result = {}
        
        # Try to extract Next.js data (embedded JSON)
        next_data_match = re.search(
            r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        if next_data_match:
            try:
                next_data = json.loads(next_data_match.group(1))
                props = next_data.get("props", {}).get("pageProps", {})
                brand_data = props.get("brand", props.get("brandData", {}))
                
                if brand_data:
                    result = {
                        "name": brand_data.get("name", ""),
                        "overall_rating": brand_data.get("ethicalRating"),
                        "rating_label": brand_data.get("ethicalLabel", ""),
                        "people_rating": brand_data.get("labourRating"),
                        "planet_rating": brand_data.get("environmentRating"),
                        "animal_rating": brand_data.get("animalRating"),
                        "categories": brand_data.get("categories", []),
                        "price_range": brand_data.get("price", ""),
                        "url": url,
                    }
                    return result
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Fallback: parse from HTML content
        # Look for rating patterns in the page
        rating_match = re.search(r'"rating"\s*:\s*(\d)', html)
        if rating_match:
            result["overall_rating"] = int(rating_match.group(1))
        
        # Look for rating label
        labels = ["Great", "Good", "It's a Start", "Not Good Enough", "We Avoid"]
        for label in labels:
            if label in html:
                result["rating_label"] = label
                break
        
        # People/Planet/Animal from meta or structured data
        for dim in ["People", "Planet", "Animal"]:
            dim_match = re.search(rf'{dim}.*?(\d)\s*/\s*5', html)
            if dim_match:
                result[f"{dim.lower()}_rating"] = int(dim_match.group(1))
        
        if result and (result.get("overall_rating") or result.get("rating_label")):
            result["url"] = url
            return result
        
        # Check if the brand exists but we couldn't parse it
        if len(html) > 10000:
            return {"url": url, "parse_error": True, "page_size": len(html)}
        
        return None
        
    except requests.RequestException as e:
        log.debug(f"Request failed for {goy_slug}: {e}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Scrape Good On You ratings for ThreadGrade brands")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    brands = load_brands()
    if args.limit > 0:
        brands = brands[:args.limit]
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "ThreadGrade/1.0 (FinMango 501c3 research; contact@finmango.org)",
        "Accept": "text/html,application/xhtml+xml",
    })
    
    stats = {"processed": 0, "found": 0, "not_found": 0, "skipped": 0}
    
    # Track unique GOY slugs to avoid duplicate requests
    seen_slugs = set()
    
    for brand in tqdm(brands, desc="Scraping Good On You"):
        slug = brand["slug"]
        output_file = OUTPUT_DIR / f"{slug}.json"
        
        if output_file.exists() and not args.force:
            stats["skipped"] += 1
            continue
        
        goy_slug = get_goy_slug(brand)
        
        # Avoid duplicate requests for store-brand variants (e.g., Target sub-brands)
        if goy_slug in seen_slugs:
            # Copy data from the first variant
            parent_file = OUTPUT_DIR / f"{[b['slug'] for b in brands if get_goy_slug(b) == goy_slug][0]}.json"
            if parent_file.exists():
                with open(parent_file) as f:
                    data = json.load(f)
                data["brand"] = brand["name"]
                data["slug"] = slug
                data["note"] = f"Rating from parent brand ({goy_slug})"
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)
                stats["processed"] += 1
                continue
        
        seen_slugs.add(goy_slug)
        time.sleep(RATE_LIMIT_SECONDS)
        
        rating_data = scrape_brand_rating(goy_slug, session)
        
        result = {
            "brand": brand["name"],
            "slug": slug,
            "goy_slug": goy_slug,
            "goy_data_available": rating_data is not None and not rating_data.get("parse_error"),
            "scraped_at": datetime.now().isoformat(),
        }
        
        if rating_data:
            result.update(rating_data)
            if not rating_data.get("parse_error"):
                stats["found"] += 1
                log.info(
                    f"{brand['name']}: "
                    f"Rating {result.get('overall_rating', '?')}/5 "
                    f"({result.get('rating_label', '?')})"
                )
            else:
                stats["not_found"] += 1
                log.debug(f"{brand['name']}: page found but couldn't parse")
        else:
            stats["not_found"] += 1
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        stats["processed"] += 1
    
    print("\n" + "=" * 60)
    print("GOOD ON YOU SCRAPER SUMMARY")
    print("=" * 60)
    print(f"  Total brands:    {len(brands)}")
    print(f"  Processed:       {stats['processed']}")
    print(f"  Ratings found:   {stats['found']}")
    print(f"  Not found:       {stats['not_found']}")
    print(f"  Skipped (cache): {stats['skipped']}")
    print(f"  Output dir:      {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
