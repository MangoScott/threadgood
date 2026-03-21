# Data Sources

## Overview

ThreadGrade's competitive moat is built on US-specific public data that global competitors don't fully leverage. This document catalogs every data source, how to access it, what it provides, and how it maps to the scoring methodology.

## Federal Data Sources

### US Customs & Border Protection — Import Records

- **URL**: https://usatrade.census.gov/ (aggregate), commercial providers for granular data
- **What it provides**: Importer name, country of origin, product category (HTS codes), volume, shipping details, and in some cases supplier/factory names
- **Update frequency**: Near-daily for commercial providers; quarterly for Census aggregate data
- **Access method**: USA Trade Online (free, aggregate), ImportGenius or Panjiva (commercial, ~$200-500/mo for granular bill-of-lading data), FOIA requests (free but slow)
- **Maps to**: WHERE dimension — supply chain geography, import volume by country, supplier identification
- **Notes**: HTS codes in chapters 61-63 cover apparel. Bill-of-lading data from commercial providers is the most granular source for identifying which factories ship to which brands. FOIA requests to CBP can yield specific import records but take 3-6 months.

### OSHA — Workplace Safety

- **URL**: https://www.osha.gov/data
- **What it provides**: Inspection records, violations (serious, willful, repeat, other), penalty amounts, abatement status, employer name and address
- **Update frequency**: Weekly
- **Access method**: OSHA API (free, well-documented), bulk data downloads (CSV)
- **Maps to**: WHO dimension — worker safety record for US-based facilities (warehouses, distribution centers, domestic manufacturing)
- **Notes**: Most useful for brands with US-based operations. Look for inspection records at known warehouse/distribution addresses. Serious and willful violations trigger red flag overrides.

### EPA — Environmental Compliance

Two key databases:

**ECHO (Enforcement and Compliance History Online)**
- **URL**: https://echo.epa.gov/
- **What it provides**: Facility-level compliance status, inspection history, enforcement actions, penalties
- **Update frequency**: Ongoing
- **Access method**: ECHO API, web search by facility name/address
- **Maps to**: WHAT dimension — chemical management, environmental compliance

**Toxics Release Inventory (TRI)**
- **URL**: https://www.epa.gov/toxics-release-inventory-tri-program
- **What it provides**: Chemical releases and waste management data reported by facilities
- **Update frequency**: Annual (with ~18 month lag)
- **Access method**: TRI Explorer (web tool), TRI API, bulk downloads
- **Maps to**: WHAT dimension — chemical releases from manufacturing/processing facilities
- **Notes**: Most relevant for brands with US manufacturing. TRI data has a significant time lag but provides the most detailed chemical release data available.

### FTC — Consumer Protection

- **URL**: https://www.ftc.gov/legal-library/browse/cases-proceedings
- **What it provides**: Enforcement actions, settlements, consent orders related to greenwashing, deceptive labeling, textile fiber content violations (Textile Act), "Made in USA" claims
- **Update frequency**: Ongoing
- **Access method**: Searchable case database, press releases, RSS feeds
- **Maps to**: Red flag system — greenwashing settlements trigger grade caps; also informs WHERE (false origin claims) and WHAT (misleading material claims)
- **Notes**: FTC has been increasingly active on greenwashing enforcement. The Green Guides provide the framework for what claims are and aren't acceptable.

### SEC EDGAR — Public Company Filings

- **URL**: https://www.sec.gov/edgar
- **What it provides**: 10-K annual reports (risk factors, supply chain disclosures), proxy statements, ESG/sustainability reports filed as exhibits, conflict minerals reports (Form SD)
- **Update frequency**: Quarterly (10-Q) and annual (10-K)
- **Access method**: EDGAR full-text search API, XBRL structured data, bulk filing downloads
- **Maps to**: All dimensions — ESG disclosures in 10-K cover labor, environment, governance. Conflict minerals reports (Form SD) cover supply chain.
- **Notes**: Only applicable to publicly traded brands or brands owned by public parent companies. The SEC's climate disclosure rules (if upheld) will make this significantly more valuable over time.

### DOL — Wage and Hour Division

- **URL**: https://www.dol.gov/agencies/whd/data
- **What it provides**: Enforcement data including employer name, back wages owed, number of employees affected, violation types (minimum wage, overtime, child labor)
- **Update frequency**: Ongoing
- **Access method**: WHD enforcement database (searchable online), bulk data downloads
- **Maps to**: WHO dimension — wage theft, minimum wage violations, child labor violations in US operations
- **Notes**: Especially relevant for brands with US-based manufacturing, warehousing, or retail operations.

## State-Level Data Sources

### California Transparency in Supply Chains Act (SB 657)

- **What it provides**: Required disclosures from retail sellers and manufacturers doing business in CA with $100M+ gross revenue. Must disclose efforts to eradicate slavery and human trafficking from supply chains.
- **Access method**: Individual company websites (mandated to post), KnowTheChain aggregates some
- **Maps to**: WHERE and WHO dimensions — supply chain transparency, forced labor risk mitigation
- **Notes**: Quality varies enormously. Some companies post detailed, substantive disclosures. Others post boilerplate. LLM analysis of disclosure quality is a high-value application.

### New York Fashion Act (if passed)

- **What it provides**: Would require fashion companies with $100M+ revenue to map supply chains, set science-based targets, report on due diligence
- **Access method**: TBD
- **Maps to**: All dimensions
- **Notes**: As of March 2026 this is still in legislative process. Worth monitoring. If passed, it would be the most comprehensive US fashion sustainability law.

## Third-Party Data Sources

### Open Apparel Registry (OAR)

- **URL**: https://openapparel.org/
- **What it provides**: Verified global database linking facilities to brands. Factory names, addresses, GPS coordinates, brand affiliations.
- **Update frequency**: Continuous (community-contributed + brand submissions)
- **Access method**: Open API (free)
- **Maps to**: WHERE dimension — factory-level supply chain mapping

### KnowTheChain

- **URL**: https://knowthechain.org/
- **What it provides**: Benchmarks of major apparel/footwear companies on forced labor practices. Scored assessments across recruitment, worker voice, monitoring, remedy.
- **Update frequency**: Biennial benchmark reports
- **Access method**: Public reports and datasets
- **Maps to**: WHO dimension — forced labor risk management

### Fashion Transparency Index (Fashion Revolution)

- **URL**: https://www.fashionrevolution.org/about/transparency/
- **What it provides**: Annual ranking of 250 major fashion brands on public disclosure across policies, governance, supply chain traceability, social/environmental practices
- **Update frequency**: Annual
- **Access method**: Public report and data downloads
- **Maps to**: All dimensions — comprehensive transparency assessment, useful as a cross-reference

### CDP (Carbon Disclosure Project)

- **URL**: https://www.cdp.net/
- **What it provides**: Climate change and water security disclosures. Detailed emissions data, targets, risk assessments.
- **Update frequency**: Annual
- **Access method**: Public scores (free), detailed responses (paid/partnership)
- **Maps to**: WHAT dimension — emissions, water use, climate targets

### Certifications and Standards

These are checked against individual brand claims and verified:

| Certification | Covers | Verification |
|--------------|--------|-------------|
| GOTS (Global Organic Textile Standard) | Organic fiber content, processing, social criteria | Publicly searchable database |
| OEKO-TEX Standard 100 | Chemical safety testing | Searchable label check |
| Bluesign | Chemical management, resource productivity, consumer safety | Partner list |
| Fair Trade Certified | Worker welfare, wages, community development | Searchable product/company database |
| B Corp | Overall social/environmental performance | B Corp directory |
| SA8000 | Social accountability (labor rights) | Certified facility database |
| Cradle to Cradle | Material health, circularity, clean air/water, social fairness | Certified product registry |
| WRAP | Social compliance (labor) | Certified facility database |

## Brand-Reported Data

### Voluntary Questionnaire

ThreadGrade provides a standardized questionnaire that brands can complete. This covers areas where public data has gaps:

- Tier 2+ supplier information
- Living wage implementation details
- Material sourcing specifics
- Circularity program metrics
- Chemical management details beyond regulatory requirements

Brands that complete the questionnaire get more complete (and likely higher) ratings, creating a positive incentive loop for transparency.

### Sustainability Reports

Most large brands publish annual sustainability reports. These are a key data source but require careful parsing:

- **LLM processing**: Claude parses reports into structured indicators, extracting concrete commitments, targets, and progress data
- **Greenwashing detection**: NLP layer flags vague language, unverifiable claims, cherry-picked metrics, and missing context
- **Cross-referencing**: Claims in sustainability reports are checked against public data (e.g., a brand claiming "zero violations" is checked against OSHA records)

## Data Pipeline Priority Order

For the MVP (Phase 1, 200 brands), data sources should be integrated in this order based on value vs. effort:

1. **Brand sustainability reports** (highest signal, LLM-parseable, covers all dimensions)
2. **OSHA enforcement data** (free API, high-value WHO signal, red flag source)
3. **Open Apparel Registry** (free API, strong WHERE signal)
4. **FTC case database** (red flag source, relatively small dataset to process)
5. **Fashion Transparency Index** (annual dataset, good cross-reference)
6. **KnowTheChain** (biennial, covers forced labor specifically)
7. **EPA ECHO** (free, environmental compliance)
8. **US Customs data** (most valuable but requires commercial access for granular data)
9. **SEC EDGAR** (only for publicly traded companies, complex to parse)
10. **DOL WHD** (valuable but smaller dataset for apparel specifically)
