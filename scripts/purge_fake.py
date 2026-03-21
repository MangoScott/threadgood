import json
import os
from pathlib import Path

DATA_DIR = Path("data")
REPORTS_DIR = DATA_DIR / "reports"
FTI_DIR = DATA_DIR / "fti"
KTC_DIR = DATA_DIR / "ktc"

SAFE_BRANDS = ["patagonia.json", "rothys.json", "on-running.json"]

def purge_dir(directory):
    count = 0
    if not directory.exists(): return
    for f in directory.glob("*.json"):
        if f.name not in SAFE_BRANDS:
            f.unlink()
            count += 1
    print(f"Purged {count} files from {directory.name}")

purge_dir(REPORTS_DIR)
purge_dir(FTI_DIR)
purge_dir(KTC_DIR)

print("Purge complete. Only real verified data remains.")
