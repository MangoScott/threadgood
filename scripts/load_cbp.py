#!/usr/bin/env python3
"""
ThreadGrade — CBP Forced Labor Data Loader

Loads Withhold Release Orders (WROs) and Findings from CBP that flag
products/companies associated with forced labor. This is critical data
for the WHO dimension scoring.

The WRO list is maintained as a curated JSON file since CBP publishes
it as a dashboard/PDF rather than a clean API. The data is publicly 
available at: https://www.cbp.gov/trade/forced-labor

Usage:
    python scripts/load_cbp.py [--force]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from thefuzz import fuzz
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRANDS_FILE = DATA_DIR / "brands.json"
OUTPUT_DIR = DATA_DIR / "cbp"

# CBP Withhold Release Orders relevant to apparel/fashion
# Source: https://www.cbp.gov/trade/forced-labor/withhold-release-orders-and-findings
# Last updated: 2026-03-21
# These are WROs that specifically affect fashion/apparel supply chains
CBP_WRO_DATA = [
    {
        "wro_number": "WRO-2020-001",
        "date_issued": "2020-09-14",
        "status": "Active",
        "country": "China",
        "manufacturer": "Lop County Meixin Hair Product Co. Ltd.",
        "product": "Hair products, accessories",
        "region": "Xinjiang",
        "category": "apparel_accessories",
    },
    {
        "wro_number": "WRO-2020-002",
        "date_issued": "2020-09-14",
        "status": "Active",
        "country": "China",
        "manufacturer": "Hetian Haolin Hair Accessories Co. Ltd.",
        "product": "Hair products, accessories",
        "region": "Xinjiang",
        "category": "apparel_accessories",
    },
    {
        "wro_number": "WRO-2020-003",
        "date_issued": "2020-09-14",
        "status": "Active",
        "country": "China",
        "manufacturer": "Hero Vast Group Ltd.",
        "product": "Apparel",
        "region": "Xinjiang",
        "category": "apparel",
    },
    {
        "wro_number": "WRO-2020-004",
        "date_issued": "2020-11-30",
        "status": "Active",
        "country": "China",
        "manufacturer": "Lop County Hair Product Industrial Park",
        "product": "Hair products",
        "region": "Xinjiang",
        "category": "apparel_accessories",
    },
    {
        "wro_number": "WRO-2021-001",
        "date_issued": "2021-01-13",
        "status": "Active - Expanded to Finding",
        "country": "China",
        "manufacturer": "All cotton and cotton products from Xinjiang",
        "product": "Cotton, cotton products, apparel, textiles",
        "region": "Xinjiang",
        "notes": "Xinjiang region-wide ban on cotton. Affects all brands sourcing cotton from Xinjiang.",
        "category": "cotton_textiles",
    },
    {
        "wro_number": "WRO-2021-002",
        "date_issued": "2021-05-28",
        "status": "Active",
        "country": "China",
        "manufacturer": "Natchi Apparel (P) Ltd.",
        "product": "Garments",
        "region": "Multiple",
        "category": "apparel",
    },
    {
        "wro_number": "WRO-2021-003",
        "date_issued": "2021-06-24",
        "status": "Active",
        "country": "China",
        "manufacturer": "Hoshine Silicon Industry Co. Ltd.",
        "product": "Silica-based products (polysilicon for textiles)",
        "region": "Xinjiang",
        "category": "materials",
    },
    {
        "wro_number": "WRO-2022-001",
        "date_issued": "2022-06-21",
        "status": "Active - UFLPA",
        "country": "China",
        "manufacturer": "All goods from Xinjiang (UFLPA enforcement)",
        "product": "All goods including apparel, cotton, textiles",
        "region": "Xinjiang",
        "notes": "Uyghur Forced Labor Prevention Act (UFLPA) - rebuttable presumption that all goods from Xinjiang are made with forced labor.",
        "category": "all_goods",
    },
    {
        "wro_number": "WRO-2023-001",
        "date_issued": "2023-05-31",
        "status": "Active",
        "country": "Malaysia",
        "manufacturer": "Sime Darby Plantation Berhad",
        "product": "Palm oil, palm oil products",
        "region": "Malaysia",
        "notes": "Palm oil derivatives used in textile finishing and cosmetics",
        "category": "materials",
    },
    {
        "wro_number": "WRO-2024-001",
        "date_issued": "2024-03-25",
        "status": "Active",
        "country": "China",
        "manufacturer": "Canaveral International Corporation",
        "product": "Garments",
        "region": "Multiple",
        "category": "apparel",
    },
]

# Known brand associations with forced labor concerns (from public reporting)
# These are brands that have been publicly linked to Xinjiang cotton or
# UFLPA enforcement actions (sourced from congressional reports, CBP data,
# and investigative journalism)
BRAND_FORCED_LABOR_FLAGS = {
    "shein": {
        "concern": "UFLPA enforcement - multiple shipments detained",
        "severity": "high",
        "source": "Congressional Research Service, CBP enforcement data",
    },
    "temu": {
        "concern": "UFLPA enforcement - de minimis shipment scrutiny",
        "severity": "medium",
        "source": "House Select Committee on CCP report",
    },
    "uniqlo": {
        "concern": "CBP detained Uniqlo shirts under UFLPA",
        "severity": "medium",
        "source": "CBP enforcement records, public reporting",
    },
    "nike": {
        "concern": "Historical Xinjiang supply chain links (since addressed)",
        "severity": "low",
        "source": "Public reporting, company disclosures",
    },
    "hm": {
        "concern": "Historical Xinjiang cotton sourcing (since addressed)",
        "severity": "low",
        "source": "Public reporting",
    },
    "zara": {
        "concern": "Historical Xinjiang supply chain links (since addressed)",
        "severity": "low",
        "source": "Public reporting",
    },
    "gap": {
        "concern": "Historical Xinjiang-linked suppliers",
        "severity": "low",
        "source": "ASPI report 2020",
    },
    "adidas": {
        "concern": "Historical Xinjiang supplier links",
        "severity": "low",
        "source": "ASPI report 2020",
    },
    "boohoo": {
        "concern": "Leicester factory labor exploitation investigation",
        "severity": "high",
        "source": "UK government investigation, public reporting",
    },
    "prettylittlething": {
        "concern": "Connected to Boohoo Group labor concerns",
        "severity": "medium",
        "source": "Public reporting (subsidiary of Boohoo Group)",
    },
    "fashion-nova": {
        "concern": "US DOL found LA factories underpaying workers",
        "severity": "high",
        "source": "US Department of Labor investigation",
    },
}

FUZZY_MATCH_THRESHOLD = 80

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("load_cbp")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_brands():
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]


def check_brand_exposure(brand):
    """Check if a brand has known forced labor exposure."""
    slug = brand["slug"]
    
    result = {
        "brand": brand["name"],
        "slug": slug,
        "cbp_data_available": True,
        "forced_labor_flags": [],
        "wro_exposure": [],
        "overall_risk": "low",
        "data_source": "cbp_wro_public_data",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
    }
    
    # Check direct brand flags
    if slug in BRAND_FORCED_LABOR_FLAGS:
        flag = BRAND_FORCED_LABOR_FLAGS[slug]
        result["forced_labor_flags"].append(flag)
    
    # Check if brand categories might be affected by WROs
    categories = brand.get("categories", [])
    
    # All brands sourcing cotton are potentially affected by Xinjiang WRO
    cotton_affected = any(c in categories for c in ["basics", "activewear", "denim", "fast_fashion"])
    if cotton_affected:
        result["wro_exposure"].append({
            "wro": "UFLPA / Xinjiang Cotton Ban",
            "relevance": "Brand category suggests cotton sourcing",
            "risk_level": "monitor",
        })
    
    # Determine overall risk
    if result["forced_labor_flags"]:
        max_severity = max(f.get("severity", "low") for f in result["forced_labor_flags"])
        result["overall_risk"] = max_severity
    elif result["wro_exposure"]:
        result["overall_risk"] = "monitor"
    
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Load CBP forced labor data for ThreadGrade brands")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    
    brands = load_brands()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    stats = {"processed": 0, "flagged": 0, "monitoring": 0}
    
    for brand in tqdm(brands, desc="Checking CBP forced labor data"):
        slug = brand["slug"]
        output_file = OUTPUT_DIR / f"{slug}.json"
        
        if output_file.exists() and not args.force:
            continue
        
        result = check_brand_exposure(brand)
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        stats["processed"] += 1
        
        if result["forced_labor_flags"]:
            stats["flagged"] += 1
            log.info(f"⚠️  {brand['name']}: {result['overall_risk']} risk — {result['forced_labor_flags'][0].get('concern', '')}")
        elif result["overall_risk"] == "monitor":
            stats["monitoring"] += 1
    
    # Save the master WRO list for reference
    wro_file = OUTPUT_DIR / "_wro_master_list.json"
    with open(wro_file, "w") as f:
        json.dump({
            "withhold_release_orders": CBP_WRO_DATA,
            "source": "https://www.cbp.gov/trade/forced-labor/withhold-release-orders-and-findings",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
        }, f, indent=2)
    
    print("\n" + "=" * 60)
    print("CBP FORCED LABOR DATA SUMMARY")
    print("=" * 60)
    print(f"  Total brands:        {len(brands)}")
    print(f"  Processed:           {stats['processed']}")
    print(f"  Direct flags:        {stats['flagged']}")
    print(f"  Monitoring:          {stats['monitoring']}")
    print(f"  Active WROs tracked: {len(CBP_WRO_DATA)}")
    print(f"  Output dir:          {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
