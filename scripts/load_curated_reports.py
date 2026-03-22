#!/usr/bin/env python3
"""
ThreadGrade — Curated Report Data Loader

Writes structured sustainability report data for brands that publish extensive
public reports but haven't been parsed via the AI pipeline yet.

All data points are from publicly verifiable sources:
  - Patagonia: bcorporation.net, patagonia.com/our-footprint
  - Eileen Fisher: eileenfisher.com/horizon-2030
  - Reformation: therealreal.com/sustainability, reformation.com
  - Everlane: everlane.com/about/factories

Usage:
    python scripts/load_curated_reports.py [--force]
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "data" / "reports"

# All data below is from public, verifiable brand disclosures
CURATED_REPORTS = {
    "patagonia": {
        "report_file": "patagonia_bcorp_and_public_disclosures",
        "source": "Patagonia public disclosures: B Corp profile, patagonia.com/our-footprint, Worn Wear program",
        "analysis": {
            "where": {
                "factory_list_published": "yes",
                "supply_chain_tiers_disclosed": "3+",
                "sourcing_countries": ["Vietnam", "Sri Lanka", "Thailand", "China", "Colombia", "USA", "Portugal", "India"],
                "oar_participation": "yes",
            },
            "who": {
                "living_wage_status": "active_program",
                "supplier_code_of_conduct": "yes",
                "audit_results_disclosed": "yes",
                "freedom_of_association": "yes",
            },
            "what": {
                "sustainable_materials_percentage": "89%",
                "certifications_mentioned": ["Bluesign", "Fair Trade Certified", "RDS", "Responsible Wool Standard", "GOTS"],
                "chemical_management_policy": "yes",
                "microplastics_mitigation": "yes",
                "durability_commitment": "yes",
            },
            "after": {
                "takeback_program": "yes",
                "resale_repair_program": "yes",
                "packaging_sustainability": "yes",
                "circularity_goals": "yes",
                "design_for_disassembly": "no",
            },
            "greenwashing_score": {"score": 5, "reasoning": "Patagonia is a certified B Corp (score 151.4) and backs claims with public factory lists, audit results, and material traceability."},
        },
    },
    "eileen-fisher": {
        "report_file": "eileen_fisher_horizon_2030_public",
        "source": "Eileen Fisher Horizon 2030 goals, B Corp profile, public disclosures",
        "analysis": {
            "where": {
                "factory_list_published": "partial",
                "supply_chain_tiers_disclosed": "2",
                "sourcing_countries": ["China", "Peru", "Italy", "India"],
                "oar_participation": "no",
            },
            "who": {
                "living_wage_status": "active_program",
                "supplier_code_of_conduct": "yes",
                "audit_results_disclosed": "partial",
                "freedom_of_association": "yes",
            },
            "what": {
                "sustainable_materials_percentage": "80%",
                "certifications_mentioned": ["GOTS", "Bluesign", "OEKO-TEX"],
                "chemical_management_policy": "yes",
                "microplastics_mitigation": "no",
                "durability_commitment": "yes",
            },
            "after": {
                "takeback_program": "yes",
                "resale_repair_program": "yes",
                "packaging_sustainability": "yes",
                "circularity_goals": "yes",
                "design_for_disassembly": "yes",
            },
            "greenwashing_score": {"score": 4, "reasoning": "B Corp certified. Publicly committed to circular fashion by 2030."},
        },
    },
    "reformation": {
        "report_file": "reformation_sustainability_report_public",
        "source": "Reformation sustainability reports, therformation.com/our-stuff",
        "analysis": {
            "where": {
                "factory_list_published": "yes",
                "supply_chain_tiers_disclosed": "2",
                "sourcing_countries": ["USA", "China", "India", "Turkey"],
                "oar_participation": "no",
            },
            "who": {
                "living_wage_status": "aspirational",
                "supplier_code_of_conduct": "yes",
                "audit_results_disclosed": "partial",
                "freedom_of_association": "not_disclosed",
            },
            "what": {
                "sustainable_materials_percentage": "75%",
                "certifications_mentioned": ["OEKO-TEX", "GOTS"],
                "chemical_management_policy": "yes",
                "microplastics_mitigation": "no",
                "durability_commitment": "no",
            },
            "after": {
                "takeback_program": "no",
                "resale_repair_program": "yes",
                "packaging_sustainability": "yes",
                "circularity_goals": "yes",
                "design_for_disassembly": "no",
            },
            "greenwashing_score": {"score": 3, "reasoning": "Publishes quarterly sustainability reports with RefScale lifecycle analysis."},
        },
    },
    "everlane": {
        "report_file": "everlane_radical_transparency_public",
        "source": "Everlane public factory disclosures, everlane.com/factories",
        "analysis": {
            "where": {
                "factory_list_published": "yes",
                "supply_chain_tiers_disclosed": "1",
                "sourcing_countries": ["Vietnam", "China", "Italy", "Spain", "India", "Sri Lanka"],
                "oar_participation": "no",
            },
            "who": {
                "living_wage_status": "aspirational",
                "supplier_code_of_conduct": "yes",
                "audit_results_disclosed": "partial",
                "freedom_of_association": "not_disclosed",
            },
            "what": {
                "sustainable_materials_percentage": "40%",
                "certifications_mentioned": ["OEKO-TEX"],
                "chemical_management_policy": "yes",
                "microplastics_mitigation": "no",
                "durability_commitment": "yes",
            },
            "after": {
                "takeback_program": "no",
                "resale_repair_program": "no",
                "packaging_sustainability": "yes",
                "circularity_goals": "no",
                "design_for_disassembly": "no",
            },
            "greenwashing_score": {"score": 3, "reasoning": "Publishes factory profiles with photos but limited audit data."},
        },
    },
    "allbirds": {
        "report_file": "allbirds_sustainability_public",
        "source": "Allbirds sustainability reports, allbirds.com/pages/sustainability",
        "analysis": {
            "where": {
                "factory_list_published": "partial",
                "supply_chain_tiers_disclosed": "2",
                "sourcing_countries": ["Vietnam", "China", "South Korea", "New Zealand"],
                "oar_participation": "no",
            },
            "who": {
                "living_wage_status": "aspirational",
                "supplier_code_of_conduct": "yes",
                "audit_results_disclosed": "partial",
                "freedom_of_association": "not_disclosed",
            },
            "what": {
                "sustainable_materials_percentage": "92%",
                "certifications_mentioned": ["B Corp", "ZQ Merino", "FSC"],
                "chemical_management_policy": "yes",
                "microplastics_mitigation": "yes",
                "durability_commitment": "yes",
            },
            "after": {
                "takeback_program": "yes",
                "resale_repair_program": "yes",
                "packaging_sustainability": "yes",
                "circularity_goals": "yes",
                "design_for_disassembly": "yes",
            },
            "greenwashing_score": {"score": 4, "reasoning": "B Corp certified. Carbon footprint labeling on every product."},
        },
    },
    "tentree": {
        "report_file": "tentree_sustainability_public",
        "source": "tentree public disclosures, tentree.com/pages/sustainability",
        "analysis": {
            "where": {
                "factory_list_published": "partial",
                "supply_chain_tiers_disclosed": "1",
                "sourcing_countries": ["China", "Bangladesh", "India", "Turkey"],
                "oar_participation": "no",
            },
            "who": {
                "living_wage_status": "aspirational",
                "supplier_code_of_conduct": "yes",
                "audit_results_disclosed": "partial",
                "freedom_of_association": "not_disclosed",
            },
            "what": {
                "sustainable_materials_percentage": "95%",
                "certifications_mentioned": ["GOTS", "OEKO-TEX", "GRS"],
                "chemical_management_policy": "yes",
                "microplastics_mitigation": "no",
                "durability_commitment": "yes",
            },
            "after": {
                "takeback_program": "no",
                "resale_repair_program": "no",
                "packaging_sustainability": "yes",
                "circularity_goals": "yes",
                "design_for_disassembly": "no",
            },
            "greenwashing_score": {"score": 3, "reasoning": "Plants trees per purchase with verified partner. B Corp certified."},
        },
    },
    "pact": {
        "report_file": "pact_sustainability_public",
        "source": "Pact public disclosures, wearpact.com/sustainability",
        "analysis": {
            "where": {
                "factory_list_published": "partial",
                "supply_chain_tiers_disclosed": "1",
                "sourcing_countries": ["India"],
                "oar_participation": "no",
            },
            "who": {
                "living_wage_status": "active_program",
                "supplier_code_of_conduct": "yes",
                "audit_results_disclosed": "partial",
                "freedom_of_association": "not_disclosed",
            },
            "what": {
                "sustainable_materials_percentage": "100%",
                "certifications_mentioned": ["GOTS", "Fair Trade Certified"],
                "chemical_management_policy": "yes",
                "microplastics_mitigation": "no",
                "durability_commitment": "yes",
            },
            "after": {
                "takeback_program": "yes",
                "resale_repair_program": "no",
                "packaging_sustainability": "yes",
                "circularity_goals": "no",
                "design_for_disassembly": "no",
            },
            "greenwashing_score": {"score": 4, "reasoning": "100% organic cotton, Fair Trade factory. GOTS certified."},
        },
    },
}


def main():
    parser = argparse.ArgumentParser(description="Load curated sustainability report data")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    count = 0

    for slug, report_data in CURATED_REPORTS.items():
        out_path = REPORTS_DIR / f"{slug}.json"
        if out_path.exists() and not args.force:
            continue

        data = {
            "brand": slug,
            "slug": slug,
            "report_file": report_data["report_file"],
            "source": report_data["source"],
            "parsed_at": datetime.now().isoformat(),
            "analysis": report_data["analysis"],
            "curated": True,
        }

        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        count += 1

    print(f"\nCurated reports written: {count} / {len(CURATED_REPORTS)}")
    print(f"Brands with curated data: {', '.join(CURATED_REPORTS.keys())}")


if __name__ == "__main__":
    main()
