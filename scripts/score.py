#!/usr/bin/env python3
"""
ThreadGrade — Scoring Engine

Reads all data sources for each brand and calculates per-dimension scores:
  WHERE (25%) — supply chain transparency
  WHO   (30%) — labor practices
  WHAT  (25%) — materials and chemicals
  AFTER (20%) — end-of-life and circularity

Applies red flag overrides, calculates confidence, and outputs grades.

Usage:
    python scripts/score.py [--force] [--brand SLUG]
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
OSHA_DIR = DATA_DIR / "osha"
OAR_DIR = DATA_DIR / "oar"
REPORTS_DIR = DATA_DIR / "reports"
FTI_DIR = DATA_DIR / "fti"
KTC_DIR = DATA_DIR / "ktc"
CBP_DIR = DATA_DIR / "cbp"
CERTS_DIR = DATA_DIR / "certs"
OUTPUT_DIR = DATA_DIR / "scores"

# Dimension weights
WEIGHTS = {
    "where": 0.25,
    "who": 0.30,
    "what": 0.25,
    "after": 0.20,
}

# Default scores when no data is available
DEFAULT_SCORES = {
    "where": 55,
    "who": 55,
    "what": 55,
    "after": 55,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("score")

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_brands() -> list[dict]:
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]

def load_json(filepath: Path) -> dict | None:
    """Load a JSON file, return None if not found."""
    if filepath.exists():
        try:
            with open(filepath) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None

def load_brand_data(slug: str) -> dict:
    """Load all data sources for a brand."""
    return {
        "osha": load_json(OSHA_DIR / f"{slug}.json"),
        "oar": load_json(OAR_DIR / f"{slug}.json"),
        "report": load_json(REPORTS_DIR / f"{slug}.json"),
        "fti": load_json(FTI_DIR / f"{slug}.json"),
        "ktc": load_json(KTC_DIR / f"{slug}.json"),
        "cbp": load_json(CBP_DIR / f"{slug}.json"),
        "certs": load_json(CERTS_DIR / f"{slug}.json"),
    }

# ---------------------------------------------------------------------------
# Dimension Scoring
# ---------------------------------------------------------------------------

def score_where(data: dict) -> tuple[float, list[str], list[str], int]:
    """
    Score the WHERE dimension (supply chain transparency).
    Returns: (score, highlights, concerns, indicators_with_data)
    """
    score = 0.0
    highlights = []
    concerns = []
    indicators = 0
    total_indicators = 5
    
    report = data.get("report", {})
    analysis = {}
    if report:
        analysis = report.get("analysis", {})
    
    oar = data.get("oar", {})
    fti = data.get("fti", {})
    
    # Factory list published: +20
    where_data = analysis.get("where", {})
    factory_list = where_data.get("factory_list_published", "not_disclosed")
    if factory_list == "yes":
        score += 20
        highlights.append("Publishes full supplier/factory list")
        indicators += 1
    elif factory_list == "partial":
        score += 10
        highlights.append("Publishes partial supplier list")
        indicators += 1
    elif factory_list == "no":
        concerns.append("Does not publish supplier list")
        indicators += 1
    
    # Multi-tier disclosure: +15
    tiers = where_data.get("supply_chain_tiers_disclosed", "not_disclosed")
    if tiers == "3+":
        score += 15
        highlights.append("Discloses 3+ supply chain tiers")
        indicators += 1
    elif tiers == "2":
        score += 10
        indicators += 1
    elif tiers == "1":
        score += 5
        indicators += 1
    elif tiers in ("0", "not_disclosed"):
        if tiers == "0":
            concerns.append("No supply chain tier disclosure")
            indicators += 1
    
    # OAR participation: +10
    oar_participation = where_data.get("oar_participation", "not_disclosed")
    oar_summary = oar.get("summary", {}) if oar else {}
    oar_facility_count = oar_summary.get("facility_count", 0)
    
    if oar_participation == "yes" or oar_facility_count > 0:
        score += 10
        indicators += 1
        if oar_facility_count > 0:
            highlights.append(f"Listed in Open Supply Hub ({oar_facility_count} facilities)")
    elif oar_participation == "no":
        indicators += 1
    
    # Countries: +5 per country (max 20)
    sourcing_countries = where_data.get("sourcing_countries", [])
    oar_countries = oar_summary.get("country_count", 0) if oar_summary else 0
    country_count = max(len(sourcing_countries), oar_countries)
    if country_count > 0:
        score += min(country_count * 5, 20)
        indicators += 1
    
    # FTI traceability score: weighted +35
    if fti and fti.get("fti_data_available"):
        fti_score = fti.get("transparency_score")
        if fti_score is not None:
            # FTI scores are 0-100, scale section to max +35 points
            score += (fti_score / 100) * 35
            indicators += 1
            if fti_score >= 50:
                highlights.append(f"FTI transparency score: {fti_score}%")
            elif fti_score < 20:
                concerns.append(f"Low FTI transparency score: {fti_score}%")
    
    # Cap at 100
    score = min(score, 100)
    
    # Apply default if no data
    if indicators == 0:
        score = DEFAULT_SCORES["where"]
    
    return score, highlights, concerns, indicators

def score_who(data: dict) -> tuple[float, list[str], list[str], int]:
    """Score the WHO dimension (labor practices)."""
    score = 0.0
    highlights = []
    concerns = []
    indicators = 0
    total_indicators = 7
    
    report = data.get("report", {})
    analysis = report.get("analysis", {}) if report else {}
    who_data = analysis.get("who", {})
    
    osha = data.get("osha", {})
    ktc = data.get("ktc", {})
    cbp = data.get("cbp", {})
    
    # Living wage: verified +25, active +15, aspirational +5
    living_wage = who_data.get("living_wage_status", "not_disclosed")
    if living_wage == "verified":
        score += 25
        highlights.append("Living wage commitment verified")
        indicators += 1
    elif living_wage == "active_program":
        score += 15
        highlights.append("Active living wage program")
        indicators += 1
    elif living_wage == "aspirational":
        score += 5
        indicators += 1
    elif living_wage == "no_mention":
        concerns.append("No living wage commitment mentioned")
        indicators += 1
    
    # Supplier code of conduct: +10
    code = who_data.get("supplier_code_of_conduct", "not_disclosed")
    if code == "yes":
        score += 10
        indicators += 1
    elif code == "no":
        concerns.append("No supplier code of conduct")
        indicators += 1
    
    # Audit results disclosed: +15
    audits = who_data.get("audit_results_disclosed", "not_disclosed")
    if audits == "yes":
        score += 15
        highlights.append("Audit results publicly disclosed")
        indicators += 1
    elif audits == "partial":
        score += 7
        indicators += 1
    elif audits == "no":
        concerns.append("Audit results not disclosed")
        indicators += 1
    
    # KnowTheChain score: scale to +30
    if ktc and ktc.get("ktc_data_available"):
        ktc_score = ktc.get("overall_score")
        if ktc_score is not None:
            # KTC scores are typically 0-100
            score += (ktc_score / 100) * 30
            indicators += 1
            if ktc_score >= 50:
                highlights.append(f"KnowTheChain score: {ktc_score}/100")
            elif ktc_score < 20:
                concerns.append(f"Low KnowTheChain score: {ktc_score}/100")
    
    # OSHA record
    if osha:
        osha_summary = osha.get("summary", {})
        serious = osha_summary.get("recent_serious_violations_3yr", osha_summary.get("serious_violations", 0))
        willful = osha_summary.get("recent_willful_violations_3yr", osha_summary.get("willful_violations", 0))
        total_inspections = osha_summary.get("total_inspections", 0)
        
        if total_inspections > 0:
            indicators += 1
            if serious == 0 and willful == 0:
                score += 10
                highlights.append("Clean OSHA safety record")
            else:
                penalty = min(serious + willful, 4) * 15  # -15 per violation, floor at 0
                score = max(score - penalty, 0)
                if serious > 0:
                    concerns.append(f"{serious} serious OSHA violation(s)")
                if willful > 0:
                    concerns.append(f"{willful} willful OSHA violation(s)")
    
    # CBP forced labor data
    if cbp and cbp.get("cbp_data_available"):
        flags = cbp.get("forced_labor_flags", [])
        risk = cbp.get("overall_risk", "low")
        indicators += 1
        if risk == "high":
            score = max(score - 30, 0)
            for fl in flags:
                concerns.append(f"Forced labor concern: {fl.get('concern', 'Unknown')}")
        elif risk == "medium":
            score = max(score - 15, 0)
            for fl in flags:
                concerns.append(f"Labor risk: {fl.get('concern', 'Unknown')}")
        elif not flags:
            score += 5
            highlights.append("No CBP forced labor flags")
    

    
    # Freedom of association: +5
    foa = who_data.get("freedom_of_association", "not_disclosed")
    if foa == "yes":
        score += 5
        indicators += 1
    
    score = min(score, 100)
    
    if indicators == 0:
        score = DEFAULT_SCORES["who"]
    
    return score, highlights, concerns, indicators

def score_what(data: dict) -> tuple[float, list[str], list[str], int]:
    """Score the WHAT dimension (materials and chemicals)."""
    score = 0.0
    highlights = []
    concerns = []
    indicators = 0
    
    report = data.get("report", {})
    analysis = report.get("analysis", {}) if report else {}
    what_data = analysis.get("what", {})
    certs_data = data.get("certs", {})
    
    # Sustainable materials percentage: scaled 0-25
    materials_pct = what_data.get("sustainable_materials_percentage", "not_disclosed")
    if materials_pct != "not_disclosed" and materials_pct is not None:
        try:
            pct = float(str(materials_pct).replace("%", ""))
            score += min((pct / 100) * 25, 25)
            indicators += 1
            if pct >= 50:
                highlights.append(f"{pct:.0f}% sustainable/certified materials")
            elif pct < 10:
                concerns.append(f"Only {pct:.0f}% sustainable materials")
        except ValueError:
            pass
    
    # Certifications from report: +10 each, max 25
    certs = what_data.get("certifications_mentioned", [])
    high_value_certs = {"GOTS", "OEKO-TEX", "Bluesign", "GRS", "RDS", "RWS"}
    cert_score = 0
    matched_certs = []
    for cert in certs:
        for hvc in high_value_certs:
            if hvc.lower() in cert.lower():
                cert_score += 10
                matched_certs.append(cert)
                break
    cert_score = min(cert_score, 25)
    if cert_score > 0:
        score += cert_score
        highlights.append(f"Certifications: {', '.join(matched_certs[:3])}")
        indicators += 1
    
    # Certifications from curated database (load_certs.py)
    if certs_data and certs_data.get("certs_data_available"):
        active = certs_data.get("active_certs", [])
        db_cert_score = certs_data.get("cert_score", 0)
        if active:
            indicators += 1
            # Scale cert_score (0-100) to 0-25 points, but don't double-count
            # with report-based certs
            bonus = min(db_cert_score * 0.25, 25)
            if cert_score == 0:  # no report-based certs, use full db bonus
                score += bonus
            else:  # report-based certs exist, add smaller bonus
                score += bonus * 0.5
            cert_names = [c["name"] for c in active[:3]]
            highlights.append(f"Verified certifications: {', '.join(cert_names)}")
    

    
    # Chemical management policy: +15
    chem = what_data.get("chemical_management_policy", "not_disclosed")
    if chem == "yes":
        score += 15
        highlights.append("Chemical management policy in place")
        indicators += 1
    elif chem == "no":
        concerns.append("No chemical management policy")
        indicators += 1
    
    # Microplastics mitigation: +10
    micro = what_data.get("microplastics_mitigation", "not_disclosed")
    if micro == "yes":
        score += 10
        highlights.append("Microplastics mitigation program")
        indicators += 1
    
    # Durability commitment: +10
    durability = what_data.get("durability_commitment", "not_disclosed")
    if durability == "yes":
        score += 10
        highlights.append("Durability/longevity commitment")
        indicators += 1
    
    score = min(score, 100)
    
    if indicators == 0:
        score = DEFAULT_SCORES["what"]
    
    return score, highlights, concerns, indicators

def score_after(data: dict) -> tuple[float, list[str], list[str], int]:
    """Score the AFTER dimension (end-of-life and circularity)."""
    score = 0.0
    highlights = []
    concerns = []
    indicators = 0
    
    report = data.get("report", {})
    analysis = report.get("analysis", {}) if report else {}
    after_data = analysis.get("after", {})
    
    # Take-back program: +25
    takeback = after_data.get("takeback_program", "not_disclosed")
    if takeback == "yes":
        score += 25
        highlights.append("Garment take-back/recycling program")
        indicators += 1
    elif takeback == "no":
        concerns.append("No take-back program")
        indicators += 1
    
    # Resale/repair program: +20
    resale = after_data.get("resale_repair_program", "not_disclosed")
    if resale == "yes":
        score += 20
        highlights.append("Resale or repair program")
        indicators += 1
    elif resale == "no":
        concerns.append("No resale/repair program")
        indicators += 1
    
    # Packaging sustainability: +15
    packaging = after_data.get("packaging_sustainability", "not_disclosed")
    if packaging == "yes":
        score += 15
        highlights.append("Sustainable packaging initiatives")
        indicators += 1
    
    # Circularity goals with timeline: +20
    circularity = after_data.get("circularity_goals", "not_disclosed")
    if circularity == "yes":
        score += 20
        highlights.append("Circularity goals with timeline")
        indicators += 1
    
    # Design for disassembly: +20
    disassembly = after_data.get("design_for_disassembly", "not_disclosed")
    if disassembly == "yes":
        score += 20
        highlights.append("Design for disassembly approach")
        indicators += 1
    
    score = min(score, 100)
    
    if indicators == 0:
        score = DEFAULT_SCORES["after"]
    
    return score, highlights, concerns, indicators

# ---------------------------------------------------------------------------
# Red Flags
# ---------------------------------------------------------------------------

def check_red_flags(data: dict) -> list[dict]:
    """Check for red flag conditions that cap scores."""
    flags = []
    
    osha = data.get("osha", {})
    report = data.get("report", {})
    analysis = report.get("analysis", {}) if report else {}
    cbp = data.get("cbp", {})
    
    # Active OSHA serious/willful violations (past 2 years)
    if osha:
        summary = osha.get("summary", {})
        recent_serious = summary.get("recent_serious_violations_3yr", 0)
        recent_willful = summary.get("recent_willful_violations_3yr", 0)
        if recent_serious > 0 or recent_willful > 0:
            flags.append({
                "type": "osha_violations",
                "description": f"Active OSHA violations: {recent_serious} serious, {recent_willful} willful",
                "cap_who": 35,
                "severity": "high",
            })
    
    # CBP forced labor flags
    if cbp and cbp.get("cbp_data_available"):
        cbp_flags = cbp.get("forced_labor_flags", [])
        cbp_risk = cbp.get("overall_risk", "low")
        if cbp_risk == "high":
            flags.append({
                "type": "forced_labor",
                "description": "CBP forced labor concern: " + "; ".join(
                    fl.get("concern", "") for fl in cbp_flags
                ),
                "cap_who": 25,
                "cap_overall": 40,
                "severity": "critical",
            })
        elif cbp_risk == "medium":
            flags.append({
                "type": "forced_labor_risk",
                "description": "CBP labor risk: " + "; ".join(
                    fl.get("concern", "") for fl in cbp_flags
                ),
                "severity": "high",
            })
    
    # Confirmed child labor
    who_data = analysis.get("who", {})
    child_labor = who_data.get("child_labor_policy", "not_disclosed")
    # Note: we don't auto-flag child_labor_policy="no" as confirmed child labor
    # That would require a separate data source (news, lawsuits, etc.)
    
    # Forced labor
    forced_labor = who_data.get("forced_labor_policy", "not_disclosed")
    
    # Greenwashing score from report
    greenwashing = analysis.get("greenwashing_score", {})
    if isinstance(greenwashing, dict):
        gs = greenwashing.get("score")
        if gs and int(gs) <= 1:
            flags.append({
                "type": "greenwashing_risk",
                "description": f"High greenwashing risk (score: {gs}/5)",
                "severity": "medium",
            })
    
    return flags

def apply_red_flags(overall: float, who_score: float, flags: list[dict]) -> tuple[float, float]:
    """Apply red flag caps to scores."""
    adjusted_who = who_score
    adjusted_overall = overall
    
    for flag in flags:
        if "cap_who" in flag:
            adjusted_who = min(adjusted_who, flag["cap_who"])
        if "cap_overall" in flag:
            adjusted_overall = min(adjusted_overall, flag["cap_overall"])
    
    return adjusted_overall, adjusted_who

# ---------------------------------------------------------------------------
# Grade Mapping
# ---------------------------------------------------------------------------

def score_to_grade(score: float) -> str:
    if score >= 80:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 35:
        return "D"
    else:
        return "F"

def grade_label(grade: str) -> str:
    labels = {
        "A": "Leading",
        "B": "Good Progress",
        "C": "Getting Started",
        "D": "Needs Work",
        "F": "Failing",
    }
    return labels.get(grade, "Unknown")

# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def calculate_confidence(total_indicators: int) -> dict:
    """Calculate confidence based on data coverage."""
    # Total possible indicators across all dimensions
    max_indicators = 25  # approximate max
    
    pct = (total_indicators / max_indicators) * 100 if max_indicators > 0 else 0
    
    if pct >= 70:
        level = "high"
    elif pct >= 40:
        level = "medium"
    else:
        level = "low"
    
    return {
        "level": level,
        "indicators_with_data": total_indicators,
        "total_possible_indicators": max_indicators,
        "data_coverage_pct": round(pct, 1),
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def score_brand(brand: dict) -> dict:
    """Calculate full scores for a single brand."""
    slug = brand["slug"]
    data = load_brand_data(slug)
    
    # Score each dimension
    where_score, where_highlights, where_concerns, where_ind = score_where(data)
    who_score, who_highlights, who_concerns, who_ind = score_who(data)
    what_score, what_highlights, what_concerns, what_ind = score_what(data)
    after_score, after_highlights, after_concerns, after_ind = score_after(data)
    
    total_indicators = where_ind + who_ind + what_ind + after_ind
    
    # Check red flags
    red_flags = check_red_flags(data)
    
    # Calculate overall (before red flag adjustments)
    overall = (
        where_score * WEIGHTS["where"]
        + who_score * WEIGHTS["who"]
        + what_score * WEIGHTS["what"]
        + after_score * WEIGHTS["after"]
    )
    
    # Apply red flag caps
    if red_flags:
        overall, who_score = apply_red_flags(overall, who_score, red_flags)
        # Recalculate overall with adjusted WHO
        overall = (
            where_score * WEIGHTS["where"]
            + who_score * WEIGHTS["who"]
            + what_score * WEIGHTS["what"]
            + after_score * WEIGHTS["after"]
        )
    
    overall = round(overall, 1)
    where_score = round(where_score, 1)
    who_score = round(who_score, 1)
    what_score = round(what_score, 1)
    after_score = round(after_score, 1)
    
    # Determine data sources used
    sources = []
    if data["osha"]:
        sources.append("osha")
    if data["oar"]:
        sources.append("oar")
    if data["report"]:
        sources.append("sustainability_report")
    if data["fti"] and data["fti"].get("fti_data_available"):
        sources.append("fti")
    if data["ktc"] and data["ktc"].get("ktc_data_available"):
        sources.append("ktc")
    if data["cbp"] and data["cbp"].get("cbp_data_available"):
        sources.append("cbp_forced_labor")
    if data["certs"] and data["certs"].get("certs_data_available"):
        sources.append("certifications")
    
    # All highlights and concerns
    all_highlights = where_highlights + who_highlights + what_highlights + after_highlights
    all_concerns = where_concerns + who_concerns + what_concerns + after_concerns
    
    return {
        "brand": brand["name"],
        "slug": slug,
        "parent": brand.get("parent", ""),
        "price_tier": brand.get("price_tier", ""),
        "categories": brand.get("categories", []),
        "overall_score": overall,
        "grade": score_to_grade(overall),
        "grade_label": grade_label(score_to_grade(overall)),
        "confidence": calculate_confidence(total_indicators),
        "dimensions": {
            "where": {
                "score": where_score,
                "grade": score_to_grade(where_score),
                "highlights": where_highlights,
                "concerns": where_concerns,
                "indicators_with_data": where_ind,
            },
            "who": {
                "score": who_score,
                "grade": score_to_grade(who_score),
                "highlights": who_highlights,
                "concerns": who_concerns,
                "indicators_with_data": who_ind,
            },
            "what": {
                "score": what_score,
                "grade": score_to_grade(what_score),
                "highlights": what_highlights,
                "concerns": what_concerns,
                "indicators_with_data": what_ind,
            },
            "after": {
                "score": after_score,
                "grade": score_to_grade(after_score),
                "highlights": after_highlights,
                "concerns": after_concerns,
                "indicators_with_data": after_ind,
            },
        },
        "red_flags": red_flags,
        "highlights": all_highlights[:5],  # top 5
        "concerns": all_concerns[:5],
        "data_sources": sources,
        "scored_at": datetime.now().isoformat(),
        "methodology_version": "1.0",
    }

def main():
    parser = argparse.ArgumentParser(description="ThreadGrade scoring engine")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--brand", type=str, help="Score a single brand by slug")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    brands = load_brands()
    
    if args.brand:
        brands = [b for b in brands if b["slug"] == args.brand]
        if not brands:
            log.error(f"Brand '{args.brand}' not found")
            sys.exit(1)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    stats = {"processed": 0, "skipped": 0}
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    
    for brand in tqdm(brands, desc="Scoring brands"):
        output_file = OUTPUT_DIR / f"{brand['slug']}.json"
        
        if output_file.exists() and not args.force:
            stats["skipped"] += 1
            continue
        
        result = score_brand(brand)
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        stats["processed"] += 1
        grade_counts[result["grade"]] += 1
        
        log.info(
            f"{brand['name']}: {result['overall_score']} ({result['grade']}) "
            f"[confidence: {result['confidence']['level']}]"
        )
    
    print("\n" + "=" * 60)
    print("SCORING ENGINE SUMMARY")
    print("=" * 60)
    print(f"  Total brands:     {len(brands)}")
    print(f"  Scored:           {stats['processed']}")
    print(f"  Skipped (cached): {stats['skipped']}")
    print(f"\n  Grade distribution:")
    for grade in ["A", "B", "C", "D", "F"]:
        bar = "█" * grade_counts[grade]
        print(f"    {grade}: {grade_counts[grade]:3d} {bar}")
    print("=" * 60)

if __name__ == "__main__":
    main()
