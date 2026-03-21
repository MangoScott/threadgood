#!/usr/bin/env python3
"""
ThreadGrade — Auto-Download Sustainability Reports
Attempts to automatically search for and download the latest
sustainability/ESG report (PDF) for each brand.

Usage:
    python3 scripts/auto_download_reports.py
"""

import json
import logging
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRANDS_FILE = DATA_DIR / "brands.json"
REPORTS_DIR = DATA_DIR / "reports"

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("downloader")

def load_brands():
    with open(BRANDS_FILE) as f:
        return json.load(f)["brands"]

def search_pdf_url(brand_name):
    """Uses a basic DuckDuckGo HTML search to find a PDF link."""
    query = f"{brand_name} sustainability OR ESG report 2023 2024 filetype:pdf"
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Simple regex to find the first PDF link in the results
            match = re.search(r'href="(https?://[^"]+\.pdf)"', html, re.IGNORECASE)
            if match:
                return match.group(1)
    except Exception as e:
        log.debug(f"Search failed for {brand_name}: {e}")
        
    return None

def download_pdf(url, filepath):
    """Download a PDF from a URL."""
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.getcode() == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.read())
                return True
    except Exception as e:
        log.debug(f"Download failed for {url}: {e}")
        
    return False

def main():
    REPORTS_DIR.mkdir(exist_ok=True, parents=True)
    brands = load_brands()
    
    print(f"Attempting to auto-download reports for {len(brands)} brands...")
    print("Please be patient, searching the web takes time to avoid rate limits.")
    print("-" * 60)
    
    success = 0
    failed = 0
    
    for brand in brands:
        slug = brand["slug"]
        name = brand["name"]
        pdf_path = REPORTS_DIR / f"{slug}.pdf"
        
        if pdf_path.exists():
            print(f"[SKIP] {name} (PDF already exists)")
            continue
            
        print(f"[SEARCH] Searching for {name}...")
        pdf_url = search_pdf_url(name)
        
        if pdf_url:
            print(f"  -> Found: {pdf_url[:60]}...")
            print(f"  -> Downloading...")
            if download_pdf(pdf_url, pdf_path):
                print(f"  ✅ Success: Saved to data/reports/{slug}.pdf")
                success += 1
            else:
                print(f"  ❌ Failed to download.")
                failed += 1
        else:
            print(f"  ❌ Could not find a PDF report.")
            failed += 1
            
        # Sleep to avoid getting banned by the search engine
        time.sleep(2)
        
    print("-" * 60)
    print(f"Auto-Download Complete!")
    print(f"Successfully downloaded: {success}")
    print(f"Failed to find/download:  {failed}")
    print(f"\nNext step: Run `make all` to parse these new PDFs and score them!")

if __name__ == "__main__":
    main()
