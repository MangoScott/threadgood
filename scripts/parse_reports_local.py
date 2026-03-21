#!/usr/bin/env python3
"""
ThreadGrade — Local Report Parser (Free/Offline)

Extracts sustainability data from PDF reports without requiring paid APIs.
Uses pdfplumber to extract text and regular expressions/keyword matching
to determine scores for the scoring engine.

While less nuanced than Claude/GPT-4, this provides a 100% free offline
alternative for the pipeline.

Usage:
    python scripts/parse_reports_local.py [--force]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("pdfplumber is required. Run: pip install pdfplumber")
    sys.exit(1)

from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRANDS_FILE = DATA_DIR / "brands.json"
REPORTS_DIR = DATA_DIR / "reports"
PDF_DIR = BASE_DIR / "reports"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("parse_local")


# ---------------------------------------------------------------------------
# Extraction Logic
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        log.error(f"Error reading {pdf_path.name}: {e}")
    return text.lower()


def analyze_text(text: str, brand_name: str) -> dict:
    """Analyze text using regex and keyword matching."""
    
    # Defaults
    analysis = {
        "where": {
            "factory_list_published": "no",
            "supply_chain_tiers_disclosed": "0",
            "oar_participation": "not_disclosed",
            "sourcing_countries": []
        },
        "who": {
            "living_wage_status": "no_mention",
            "supplier_code_of_conduct": "no",
            "audit_results_disclosed": "no",
            "freedom_of_association": "no"
        },
        "what": {
            "sustainable_materials_percentage": "not_disclosed",
            "certifications_mentioned": [],
            "chemical_management_policy": "no",
            "microplastics_mitigation": "no",
            "durability_commitment": "no"
        },
        "after": {
            "takeback_program": "no",
            "resale_repair_program": "no",
            "packaging_sustainability": "no",
            "circularity_goals": "no",
            "design_for_disassembly": "no"
        },
        "greenwashing_score": {
            "score": 3,
            "reasoning": "Default score for regex-based parsing.",
            "specific_claims_to_verify": []
        }
    }
    
    # 1. WHERE (Transparency)
    if "supplier list" in text or "factory list" in text or "tier 1 suppliers" in text:
        analysis["where"]["factory_list_published"] = "yes"
    
    if "tier 3" in text or "tier 4" in text:
        analysis["where"]["supply_chain_tiers_disclosed"] = "3+"
    elif "tier 2" in text:
        analysis["where"]["supply_chain_tiers_disclosed"] = "2"
    elif "tier 1" in text:
        analysis["where"]["supply_chain_tiers_disclosed"] = "1"
        
    if "open supply hub" in text or "open apparel registry" in text.replace("-", " "):
        analysis["where"]["oar_participation"] = "yes"
    
    # 2. WHO (Labor)
    if "living wage" in text:
        # Check if it's aspirational or active
        if "achieved living wage" in text or "paying living wage" in text:
            analysis["who"]["living_wage_status"] = "active_program"
        else:
            analysis["who"]["living_wage_status"] = "aspirational"
            
    if "code of conduct" in text or "supplier expectations" in text:
        analysis["who"]["supplier_code_of_conduct"] = "yes"
        
    if "audit results" in text or "audit findings" in text or "compliance rate" in text:
        analysis["who"]["audit_results_disclosed"] = "yes"
        
    if "freedom of association" in text or "collective bargaining" in text:
        analysis["who"]["freedom_of_association"] = "yes"
        
    # 3. WHAT (Materials)
    materials_pattern = re.search(r'(\d+)%\s*(?:of|our)?\s*(?:materials|cotton|polyester)\s*(?:are|is)?\s*(?:sustainable|preferred|recycled|organic)', text)
    if materials_pattern:
        analysis["what"]["sustainable_materials_percentage"] = f"{materials_pattern.group(1)}%"
        
    certs = []
    if "gots" in text or "global organic textile standard" in text: certs.append("GOTS")
    if "bluesign" in text: certs.append("Bluesign")
    if "oeko-tex" in text or "oekotex" in text: certs.append("OEKO-TEX")
    if "fair trade" in text: certs.append("Fair Trade")
    analysis["what"]["certifications_mentioned"] = certs
    
    if "chemical management" in text or "zdhc" in text or "mrs" in text or "restricted substances" in text:
        analysis["what"]["chemical_management_policy"] = "yes"
        
    if "microplastic" in text or "microfibre" in text or "fiber shedding" in text:
        analysis["what"]["microplastics_mitigation"] = "yes"
        
    if "durability" in text or "longevity" in text or "built to last" in text:
        analysis["what"]["durability_commitment"] = "yes"
        
    # 4. AFTER (Circularity)
    if "take-back" in text or "take back" in text or "collecting garments" in text or "recycling program" in text:
        analysis["after"]["takeback_program"] = "yes"
        
    if "resale" in text or "second hand" in text or "repair" in text or "worn wear" in text:
        analysis["after"]["resale_repair_program"] = "yes"
        
    if "sustainable packaging" in text or "recycled packaging" in text or "fsc certified packaging" in text:
        analysis["after"]["packaging_sustainability"] = "yes"
        
    if "circular" in text and ("goal" in text or "target" in text or "2025" in text or "2030" in text):
        analysis["after"]["circularity_goals"] = "yes"
        
    if "design for disassembly" in text:
        analysis["after"]["design_for_disassembly"] = "yes"
        
    # 5. Greenwashing (Simple heuristic)
    buzzwords = text.count("sustainable") + text.count("eco-friendly") + text.count("green")
    metrics = text.count("reduced by") + text.count("%") + text.count("tonnes")
    
    if buzzwords > 20 and metrics < 5:
        analysis["greenwashing_score"]["score"] = 1
        analysis["greenwashing_score"]["reasoning"] = "High ratio of buzzwords to actual metrics/data."
    elif metrics > 20:
        analysis["greenwashing_score"]["score"] = 4
        analysis["greenwashing_score"]["reasoning"] = "Contains significant numerical data and metrics."
        
    return analysis


def load_brands():
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]


def main():
    parser = argparse.ArgumentParser(description="Parse PDF reports locally without APIs")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    
    brands = load_brands()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if there are any PDFs
    if not PDF_DIR.exists():
        log.error(f"Please create a '{PDF_DIR}' directory and add sustainability PDFs (named brand-slug.pdf).")
        sys.exit(1)
        
    pdfs = list(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        log.info(f"No PDFs found in {PDF_DIR}. Place files like 'patagonia.pdf' there.")
        sys.exit(0)
        
    log.info(f"Found {len(pdfs)} PDF reports.")
    
    for pdf_path in tqdm(pdfs, desc="Parsing local PDFs"):
        slug = pdf_path.stem
        output_file = REPORTS_DIR / f"{slug}.json"
        
        if output_file.exists() and not args.force:
            continue
            
        # Find matching brand
        brand = next((b for b in brands if b["slug"] == slug), None)
        if not brand:
            log.warning(f"File {pdf_path.name} doesn't match a known brand slug. Processing anyway.")
            brand_name = slug.replace("-", " ").title()
        else:
            brand_name = brand["name"]
            
        text = extract_text_from_pdf(pdf_path)
        if not text:
            continue
            
        analysis = analyze_text(text, brand_name)
        
        result = {
            "brand": brand_name,
            "slug": slug,
            "report_file": pdf_path.name,
            "parsed_at": datetime.now().isoformat(),
            "parser_version": "local-regex-1.0",
            "analysis": analysis
        }
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
            
        log.info(f"✅ Parsed {brand_name}")

if __name__ == "__main__":
    main()
