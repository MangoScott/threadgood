#!/usr/bin/env python3
"""
ThreadGrade — Certifications Database

Checks brands against known sustainability certifications and ethical 
standards. Uses a curated database of certified brands compiled from
public certification directories.

Certifications tracked:
  - B Corp
  - Fair Trade
  - GOTS (Global Organic Textile Standard)
  - Bluesign
  - SA8000 (social accountability)
  - WRAP (Worldwide Responsible Accredited Production)

Usage:
    python scripts/load_certs.py [--force]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRANDS_FILE = DATA_DIR / "brands.json"
OUTPUT_DIR = DATA_DIR / "certs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("load_certs")


# ---------------------------------------------------------------------------
# Certifications Database
# Compiled from public directories:
#   - B Corp: https://www.bcorporation.net/en-us/find-a-b-corp/
#   - Fair Trade: https://www.fairtradecertified.org/
#   - Bluesign: https://www.bluesign.com/
#   - GOTS: https://global-standard.org/
# ---------------------------------------------------------------------------

CERTIFICATIONS_DB = {
    "patagonia": {
        "b_corp": {"certified": True, "since": 2012, "score": 151.4},
        "fair_trade": {"certified": True, "program": "Fair Trade Certified sewing"},
        "bluesign": {"certified": True, "note": "Bluesign system partner"},
        "gots": {"certified": False},
    },
    "eileen-fisher": {
        "b_corp": {"certified": True, "since": 2015, "score": 93.5},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": True},
        "gots": {"certified": True, "note": "Organic cotton products"},
    },
    "allbirds": {
        "b_corp": {"certified": True, "since": 2016, "score": 89.4},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": False},
        "gots": {"certified": False},
    },
    "pact": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": True, "program": "Fair Trade Factory Certified"},
        "bluesign": {"certified": False},
        "gots": {"certified": True, "note": "GOTS certified organic cotton"},
    },
    "tentree": {
        "b_corp": {"certified": True, "since": 2020, "score": 83.1},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": True, "note": "Select products"},
        "gots": {"certified": False},
    },
    "reformation": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": False},
        "gots": {"certified": True, "note": "Select fabrics"},
        "climate_neutral": {"certified": True, "since": 2019},
    },
    "everlane": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": True, "note": "Select products"},
        "gots": {"certified": False},
    },
    "nike": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": True, "note": "Bluesign system partner since 2010"},
        "gots": {"certified": False},
    },
    "adidas": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": True, "note": "Bluesign system partner"},
        "gots": {"certified": False},
    },
    "levis": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": False},
        "gots": {"certified": False},
        "oeko_tex": {"certified": True, "note": "Select products"},
    },
    "puma": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": True, "note": "Bluesign system partner"},
        "gots": {"certified": False},
    },
    "hm": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": True, "program": "Fair Trade cotton collection"},
        "bluesign": {"certified": False},
        "gots": {"certified": True, "note": "Conscious Collection"},
        "oeko_tex": {"certified": True},
    },
    "madewell": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": True, "program": "Fair Trade Certified denim"},
        "bluesign": {"certified": False},
        "gots": {"certified": False},
    },
    "thredup": {
        "b_corp": {"certified": True, "since": 2021},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": False},
        "gots": {"certified": False},
    },
    "columbia-sportswear": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": True, "note": "Bluesign system partner"},
        "gots": {"certified": False},
    },
    "the-north-face": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": True, "note": "System partner"},
        "gots": {"certified": False},
    },
    "lululemon": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": True, "program": "Fair Trade Certified sewing"},
        "bluesign": {"certified": True},
        "gots": {"certified": False},
    },
    "new-balance": {
        "b_corp": {"certified": False},
        "fair_trade": {"certified": False},
        "bluesign": {"certified": True, "note": "Select products"},
        "gots": {"certified": False},
    },
}

# Cert weights for scoring (how much each cert matters)
CERT_WEIGHTS = {
    "b_corp": {"points": 15, "label": "B Corporation"},
    "fair_trade": {"points": 12, "label": "Fair Trade Certified"},
    "bluesign": {"points": 8, "label": "Bluesign Partner"},
    "gots": {"points": 10, "label": "GOTS Certified"},
    "oeko_tex": {"points": 6, "label": "OEKO-TEX Certified"},
    "climate_neutral": {"points": 8, "label": "Climate Neutral Certified"},
    "sa8000": {"points": 12, "label": "SA8000 Certified"},
    "wrap": {"points": 8, "label": "WRAP Certified"},
}


def load_brands():
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]


def check_brand_certs(brand):
    """Look up certifications for a brand."""
    slug = brand["slug"]
    
    result = {
        "brand": brand["name"],
        "slug": slug,
        "certs_data_available": slug in CERTIFICATIONS_DB,
        "certifications": {},
        "active_certs": [],
        "cert_score": 0,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "data_source": "curated_certification_directories",
    }
    
    if slug not in CERTIFICATIONS_DB:
        return result
    
    brand_certs = CERTIFICATIONS_DB[slug]
    result["certifications"] = brand_certs
    
    total_score = 0
    for cert_key, cert_data in brand_certs.items():
        if cert_data.get("certified"):
            weight = CERT_WEIGHTS.get(cert_key, {})
            points = weight.get("points", 5)
            label = weight.get("label", cert_key)
            total_score += points
            result["active_certs"].append({
                "name": label,
                "key": cert_key,
                "points": points,
                "details": cert_data,
            })
    
    result["cert_score"] = min(total_score, 100)  # cap at 100
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Check certifications for ThreadGrade brands")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    
    brands = load_brands()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    stats = {"processed": 0, "with_certs": 0}
    
    for brand in tqdm(brands, desc="Checking certifications"):
        slug = brand["slug"]
        output_file = OUTPUT_DIR / f"{slug}.json"
        
        if output_file.exists() and not args.force:
            continue
        
        result = check_brand_certs(brand)
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        stats["processed"] += 1
        
        if result["active_certs"]:
            stats["with_certs"] += 1
            cert_names = [c["name"] for c in result["active_certs"]]
            log.info(f"✅ {brand['name']}: {', '.join(cert_names)} (score: {result['cert_score']})")
    
    print("\n" + "=" * 60)
    print("CERTIFICATIONS SUMMARY")
    print("=" * 60)
    print(f"  Total brands:         {len(brands)}")
    print(f"  Processed:            {stats['processed']}")
    print(f"  With certifications:  {stats['with_certs']}")
    print(f"  In database:          {len(CERTIFICATIONS_DB)}")
    print(f"  Output dir:           {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
