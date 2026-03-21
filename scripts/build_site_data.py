#!/usr/bin/env python3
"""
ThreadGrade — Site Data Generator

Reads all scored brand data and generates:
1. data/site/brands.json — summary of all brands for the frontend
2. data/site/brands/{slug}.json — detailed view per brand
3. brands.json in repo root — copy for static site

Usage:
    python scripts/build_site_data.py [--force]
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
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
SCORES_DIR = DATA_DIR / "scores"
OSHA_DIR = DATA_DIR / "osha"
OAR_DIR = DATA_DIR / "oar"
REPORTS_DIR = DATA_DIR / "reports"
FTI_DIR = DATA_DIR / "fti"
KTC_DIR = DATA_DIR / "ktc"
SITE_DIR = DATA_DIR / "site"
SITE_BRANDS_DIR = SITE_DIR / "brands"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("build_site")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_brands() -> list[dict]:
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]


def load_json(filepath: Path) -> dict | None:
    if filepath.exists():
        try:
            with open(filepath) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def build_brand_summary(brand: dict, score_data: dict) -> dict:
    """Build the summary object for the site-wide brands.json."""
    dims = score_data.get("dimensions", {})
    
    return {
        "name": brand["name"],
        "slug": brand["slug"],
        "parent": brand.get("parent", ""),
        "price_tier": brand.get("price_tier", ""),
        "categories": brand.get("categories", []),
        "grade": score_data.get("grade", "F"),
        "overall_score": score_data.get("overall_score", 0),
        "confidence": score_data.get("confidence", {}).get("level", "low"),
        "dimensions": {
            "where": {
                "score": dims.get("where", {}).get("score", 0),
                "grade": dims.get("where", {}).get("grade", "F"),
            },
            "who": {
                "score": dims.get("who", {}).get("score", 0),
                "grade": dims.get("who", {}).get("grade", "F"),
            },
            "what": {
                "score": dims.get("what", {}).get("score", 0),
                "grade": dims.get("what", {}).get("grade", "F"),
            },
            "after": {
                "score": dims.get("after", {}).get("score", 0),
                "grade": dims.get("after", {}).get("grade", "F"),
            },
        },
        "red_flags": [f["type"] for f in score_data.get("red_flags", [])],
        "highlights": score_data.get("highlights", [])[:3],
        "concerns": score_data.get("concerns", [])[:3],
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "data_sources": score_data.get("data_sources", []),
    }


def build_brand_detail(brand: dict, score_data: dict) -> dict:
    """Build the detailed object for individual brand pages."""
    slug = brand["slug"]
    
    # Load source data for the detail view
    osha_data = load_json(OSHA_DIR / f"{slug}.json")
    oar_data = load_json(OAR_DIR / f"{slug}.json")
    report_data = load_json(REPORTS_DIR / f"{slug}.json")
    fti_data = load_json(FTI_DIR / f"{slug}.json")
    ktc_data = load_json(KTC_DIR / f"{slug}.json")
    
    detail = {
        "name": brand["name"],
        "slug": slug,
        "parent": brand.get("parent", ""),
        "price_tier": brand.get("price_tier", ""),
        "categories": brand.get("categories", []),
        "overall_score": score_data.get("overall_score", 0),
        "grade": score_data.get("grade", "F"),
        "grade_label": score_data.get("grade_label", ""),
        "confidence": score_data.get("confidence", {}),
        "dimensions": score_data.get("dimensions", {}),
        "red_flags": score_data.get("red_flags", []),
        "highlights": score_data.get("highlights", []),
        "concerns": score_data.get("concerns", []),
        "data_sources": score_data.get("data_sources", []),
        "methodology_version": score_data.get("methodology_version", "1.0"),
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        
        # Source data summaries
        "source_data": {},
    }
    
    # OSHA summary
    if osha_data:
        osha_summary = osha_data.get("summary", {})
        detail["source_data"]["osha"] = {
            "total_inspections": osha_summary.get("total_inspections", 0),
            "serious_violations": osha_summary.get("serious_violations", 0),
            "willful_violations": osha_summary.get("willful_violations", 0),
            "total_penalties": osha_summary.get("total_penalties", 0),
            "most_recent_inspection": osha_summary.get("most_recent_inspection"),
            "states": osha_summary.get("states", []),
        }
    
    # OAR summary
    if oar_data:
        oar_summary = oar_data.get("summary", {})
        detail["source_data"]["oar"] = {
            "facility_count": oar_summary.get("facility_count", 0),
            "country_count": oar_summary.get("country_count", 0),
            "countries": oar_summary.get("countries", []),
        }
    
    # Report summary
    if report_data:
        analysis = report_data.get("analysis", {})
        detail["source_data"]["sustainability_report"] = {
            "report_file": report_data.get("report_file", ""),
            "parsed_at": report_data.get("parsed_at", ""),
            "where": analysis.get("where", {}),
            "who": analysis.get("who", {}),
            "what": analysis.get("what", {}),
            "after": analysis.get("after", {}),
            "targets": analysis.get("targets", []),
            "certifications": analysis.get("certifications_claimed", []),
            "greenwashing_score": analysis.get("greenwashing_score", {}),
        }
    
    # FTI summary
    if fti_data and fti_data.get("fti_data_available"):
        detail["source_data"]["fti"] = {
            "transparency_score": fti_data.get("transparency_score"),
            "rank": fti_data.get("rank"),
            "section_scores": fti_data.get("section_scores", {}),
        }
    
    # KTC summary
    if ktc_data and ktc_data.get("ktc_data_available"):
        detail["source_data"]["ktc"] = {
            "overall_score": ktc_data.get("overall_score"),
            "theme_scores": ktc_data.get("theme_scores", {}),
        }
    
    return detail


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate ThreadGrade site data")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    
    brands = load_brands()
    
    # Ensure output dirs
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    SITE_BRANDS_DIR.mkdir(parents=True, exist_ok=True)
    
    all_summaries = []
    stats = {"processed": 0, "no_score": 0}
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    
    for brand in tqdm(brands, desc="Building site data"):
        slug = brand["slug"]
        
        # Load score data
        score_data = load_json(SCORES_DIR / f"{slug}.json")
        
        if not score_data:
            log.warning(f"No score data for {brand['name']} — run `make score` first")
            stats["no_score"] += 1
            # Create a minimal entry with defaults
            score_data = {
                "overall_score": 0,
                "grade": "F",
                "grade_label": "Not Yet Rated",
                "confidence": {"level": "low", "indicators_with_data": 0},
                "dimensions": {
                    "where": {"score": 0, "grade": "F"},
                    "who": {"score": 0, "grade": "F"},
                    "what": {"score": 0, "grade": "F"},
                    "after": {"score": 0, "grade": "F"},
                },
                "red_flags": [],
                "highlights": [],
                "concerns": ["Insufficient data to generate rating"],
                "data_sources": [],
            }
        
        # Build summary for brands.json
        summary = build_brand_summary(brand, score_data)
        all_summaries.append(summary)
        grade_counts[summary["grade"]] += 1
        
        # Build and save detail JSON
        detail = build_brand_detail(brand, score_data)
        detail_file = SITE_BRANDS_DIR / f"{slug}.json"
        with open(detail_file, "w") as f:
            json.dump(detail, f, indent=2, default=str)
        
        stats["processed"] += 1
    
    # Sort summaries by overall score (descending)
    all_summaries.sort(key=lambda x: x["overall_score"], reverse=True)
    
    # Build the main brands.json
    site_data = {
        "brands": all_summaries,
        "metadata": {
            "total_brands": len(all_summaries),
            "methodology_version": "1.0",
            "last_build": datetime.now().strftime("%Y-%m-%d"),
            "grade_distribution": grade_counts,
            "price_tier_counts": {},
        },
    }
    
    # Count price tiers
    for s in all_summaries:
        tier = s.get("price_tier", "unknown")
        site_data["metadata"]["price_tier_counts"][tier] = (
            site_data["metadata"]["price_tier_counts"].get(tier, 0) + 1
        )
    
    # Save site brands.json
    site_brands_file = SITE_DIR / "brands.json"
    with open(site_brands_file, "w") as f:
        json.dump(site_data, f, indent=2, default=str)
    
    # Copy to repo root for static site
    root_brands_file = BASE_DIR / "brands.json"
    shutil.copy2(site_brands_file, root_brands_file)
    
    log.info(f"Wrote {site_brands_file}")
    log.info(f"Copied to {root_brands_file}")
    
    print("\n" + "=" * 60)
    print("SITE DATA GENERATOR SUMMARY")
    print("=" * 60)
    print(f"  Total brands:         {len(brands)}")
    print(f"  Processed:            {stats['processed']}")
    print(f"  Missing scores:       {stats['no_score']}")
    print(f"\n  Grade distribution:")
    for grade in ["A", "B", "C", "D", "F"]:
        bar = "█" * grade_counts[grade]
        print(f"    {grade}: {grade_counts[grade]:3d} {bar}")
    print(f"\n  Output files:")
    print(f"    {site_brands_file}")
    print(f"    {SITE_BRANDS_DIR}/ ({stats['processed']} files)")
    print(f"    {root_brands_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
