#!/usr/bin/env python3
"""
ThreadGrade — Sustainability Report Parser

Extracts structured sustainability indicators from brand PDF reports
using pdfplumber for text extraction and Claude API for analysis.

Place PDF reports in reports/{brand-slug}.pdf or reports/{brand-slug}/
Outputs structured JSON to data/reports/{brand-slug}.json

Usage:
    python scripts/parse_reports.py [--force] [--limit N] [--brand SLUG]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRANDS_FILE = DATA_DIR / "brands.json"
OUTPUT_DIR = DATA_DIR / "reports"
REPORTS_DIR = BASE_DIR / "reports"
PROMPTS_DIR = BASE_DIR / "prompts"

load_dotenv(BASE_DIR / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TEXT_LENGTH = 150000  # chars — keep well under Claude's context window

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("parse_reports")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_brands() -> list[dict]:
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]


def load_system_prompt() -> str:
    prompt_file = PROMPTS_DIR / "report_parser.txt"
    if not prompt_file.exists():
        log.error(f"System prompt not found at {prompt_file}")
        sys.exit(1)
    return prompt_file.read_text()


def find_report_pdf(slug: str) -> Path | None:
    """Find a PDF report for the given brand slug."""
    # Check for direct PDF
    pdf_path = REPORTS_DIR / f"{slug}.pdf"
    if pdf_path.exists():
        return pdf_path
    
    # Check for folder with PDFs
    brand_dir = REPORTS_DIR / slug
    if brand_dir.is_dir():
        pdfs = list(brand_dir.glob("*.pdf"))
        if pdfs:
            # Return the most recently modified one
            return max(pdfs, key=lambda p: p.stat().st_mtime)
    
    # Check case-insensitive
    for f in REPORTS_DIR.glob("*.pdf"):
        if f.stem.lower() == slug.lower():
            return f
    
    return None


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF using pdfplumber."""
    log.info(f"  Extracting text from {pdf_path.name}")
    
    pages_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(f"--- PAGE {i + 1} ---\n{text}")
    except Exception as e:
        log.error(f"  Failed to extract text from {pdf_path.name}: {e}")
        return ""
    
    full_text = "\n\n".join(pages_text)
    
    # Truncate if too long (keep beginning and end)
    if len(full_text) > MAX_TEXT_LENGTH:
        half = MAX_TEXT_LENGTH // 2
        full_text = (
            full_text[:half]
            + f"\n\n[... TRUNCATED {len(full_text) - MAX_TEXT_LENGTH} characters ...]\n\n"
            + full_text[-half:]
        )
    
    log.info(f"  Extracted {len(full_text):,} characters from {len(pages_text)} pages")
    return full_text


def analyze_with_claude(text: str, brand_name: str, system_prompt: str) -> dict:
    """Send extracted text to Claude for structured analysis."""
    try:
        import anthropic
    except ImportError:
        log.error("anthropic package not installed. Run: pip install anthropic")
        return {}
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    user_message = (
        f"Analyze this sustainability report for the brand '{brand_name}'. "
        f"Extract all indicators per the schema in your instructions.\n\n"
        f"REPORT TEXT:\n\n{text}"
    )
    
    log.info(f"  Sending {len(text):,} chars to Claude ({CLAUDE_MODEL})...")
    
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        
        response_text = response.content[0].text.strip()
        
        # Try to parse as JSON
        # Remove markdown code block wrappers if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        
        result = json.loads(response_text)
        log.info(f"  Successfully parsed Claude response")
        return result
        
    except json.JSONDecodeError as e:
        log.error(f"  Failed to parse Claude response as JSON: {e}")
        log.debug(f"  Raw response: {response_text[:500]}")
        return {"raw_response": response_text, "parse_error": str(e)}
    except Exception as e:
        log.error(f"  Claude API call failed: {e}")
        return {"api_error": str(e)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Parse sustainability reports with Claude")
    parser.add_argument("--force", action="store_true", help="Re-parse even if cached")
    parser.add_argument("--limit", type=int, default=0, help="Limit brands to process")
    parser.add_argument("--brand", type=str, help="Process a single brand by slug")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check API key
    if not ANTHROPIC_API_KEY:
        log.error(
            "ANTHROPIC_API_KEY not set in .env. "
            "Get one at https://console.anthropic.com"
        )
        sys.exit(1)
    
    # Load data
    brands = load_brands()
    system_prompt = load_system_prompt()
    
    # Filter brands
    if args.brand:
        brands = [b for b in brands if b["slug"] == args.brand]
        if not brands:
            log.error(f"Brand '{args.brand}' not found in brands.json")
            sys.exit(1)
    elif args.limit > 0:
        brands = brands[:args.limit]
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "processed": 0,
        "no_pdf": 0,
        "skipped_cached": 0,
        "errors": 0,
    }
    
    for brand in tqdm(brands, desc="Parsing reports"):
        slug = brand["slug"]
        output_file = OUTPUT_DIR / f"{slug}.json"
        
        if output_file.exists() and not args.force:
            stats["skipped_cached"] += 1
            continue
        
        # Find PDF
        pdf_path = find_report_pdf(slug)
        if not pdf_path:
            stats["no_pdf"] += 1
            log.debug(f"No PDF found for {brand['name']} (expected reports/{slug}.pdf)")
            continue
        
        try:
            # Extract text
            text = extract_pdf_text(pdf_path)
            if not text:
                log.warning(f"No text extracted from {pdf_path}")
                stats["errors"] += 1
                continue
            
            # Analyze with Claude
            analysis = analyze_with_claude(text, brand["name"], system_prompt)
            
            result = {
                "brand": brand["name"],
                "slug": slug,
                "parent": brand.get("parent", ""),
                "data_source": "sustainability_report",
                "report_file": pdf_path.name,
                "parsed_at": datetime.now().isoformat(),
                "text_length": len(text),
                "analysis": analysis,
            }
            
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2, default=str)
            
            stats["processed"] += 1
            log.info(f"✓ {brand['name']}: parsed successfully")
            
        except Exception as e:
            stats["errors"] += 1
            log.error(f"Error processing {brand['name']}: {e}")
    
    print("\n" + "=" * 60)
    print("REPORT PARSER SUMMARY")
    print("=" * 60)
    print(f"  Total brands:           {len(brands)}")
    print(f"  Reports parsed:         {stats['processed']}")
    print(f"  No PDF found:           {stats['no_pdf']}")
    print(f"  Skipped (cached):       {stats['skipped_cached']}")
    print(f"  Errors:                 {stats['errors']}")
    print(f"  Report dir:             {REPORTS_DIR}")
    print(f"  Output dir:             {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
