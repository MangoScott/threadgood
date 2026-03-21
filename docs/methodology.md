# Rating Methodology

## Overview

ThreadGrade rates US clothing brands on a letter-grade scale (A through F) across four dimensions, weighted and combined into an overall score. Every rating includes a price tier so users can find the best ethical option at their actual budget.

## The Four Dimensions

### WHERE (25% weight)

Supply chain transparency and geography.

**Key indicators:**
- Percentage of supply chain disclosed (factory names, locations, tiers)
- Countries of origin for finished goods and raw materials
- Number of supply chain tiers with visibility
- Participation in Open Apparel Registry or equivalent
- CA SB 657 disclosure quality (for applicable brands)

**Primary data sources:**
- US Customs import records (country of origin, importer, volume)
- CA Transparency in Supply Chains Act filings
- Open Apparel Registry factory data
- Brand sustainability reports (parsed by LLM)

**Scoring logic:**
- 0–20: No supply chain disclosure. No factory list. No country-of-origin transparency beyond label requirements.
- 21–40: Partial disclosure. Some countries listed. No factory-level transparency.
- 41–60: Tier 1 factories disclosed. Some information on lower tiers. Participates in at least one transparency initiative.
- 61–80: Full Tier 1 and partial Tier 2 disclosure. Factory audit results shared. Regular updates.
- 81–100: Full multi-tier supply chain transparency. Factory names, addresses, audit results all public. Active participation in Open Apparel Registry.

### WHO (30% weight)

Labor practices and worker welfare. This is the highest-weighted dimension because labor exploitation is the single largest human impact of the fashion industry.

**Key indicators:**
- Living wage commitments and evidence of implementation
- OSHA violation history (for US facilities)
- DOL Wage & Hour violations
- Child labor and forced labor risk indicators
- Worker safety policies and audit results
- Freedom of association / union rights
- Gender equality policies
- Supplier code of conduct quality and enforcement

**Primary data sources:**
- OSHA inspection and violation records
- DOL Wage & Hour enforcement database
- KnowTheChain forced labor benchmarks
- Fair Labor Association reports
- Brand disclosures (parsed by LLM)
- News coverage of labor incidents

**Scoring logic:**
- 0–20: No labor policies disclosed. Active OSHA/DOL violations. Sourcing from high-risk regions with no mitigation.
- 21–40: Basic code of conduct exists but no evidence of enforcement. No audit results shared.
- 41–60: Code of conduct with some audit data. Living wage mentioned but not verified. Some corrective action evidence.
- 61–80: Strong labor policies with third-party audit results. Living wage programs in progress. Worker grievance mechanisms in place.
- 81–100: Industry-leading labor practices. Verified living wages. Worker empowerment programs. Clean OSHA/DOL record. Third-party certified (Fair Trade, SA8000, etc.).

### WHAT (25% weight)

Materials, chemicals, and durability.

**Key indicators:**
- Percentage of sustainable/certified materials (organic, recycled, etc.)
- Chemical management policies (ZDHC, Bluesign, OEKO-TEX)
- EPA compliance record for US facilities
- Fiber/material transparency at product level
- Durability commitments or testing
- Microplastics/microfiber mitigation

**Primary data sources:**
- Brand materials disclosures
- Certifications (GOTS, OEKO-TEX, Bluesign, Cradle to Cradle)
- EPA ECHO database (enforcement actions)
- EPA Toxics Release Inventory (chemical releases)
- Product-level material composition data

**Scoring logic:**
- 0–20: No materials transparency. No certifications. Active EPA violations.
- 21–40: Basic fiber content disclosed (as legally required). No sustainability-focused material choices.
- 41–60: Some certified or preferred materials. Chemical management policy exists. At least one material certification.
- 61–80: Majority of materials from preferred sources. Strong chemical management with third-party verification. Durability testing.
- 81–100: Industry-leading materials program. Comprehensive certifications. Full chemical transparency. Innovation in sustainable materials.

### AFTER (20% weight)

End-of-life and circularity. This is the lowest-weighted dimension because circularity infrastructure is still nascent, but it's included because it's increasingly important and rewards forward-thinking brands.

**Key indicators:**
- Take-back or recycling program availability
- Resale/repair infrastructure
- Packaging sustainability
- Product designed for disassembly/recyclability
- Waste reduction targets and progress
- Extended producer responsibility engagement

**Primary data sources:**
- Brand circularity program disclosures
- EPA textile waste data
- Packaging disclosures
- Resale platform partnerships
- Industry circularity initiative participation

**Scoring logic:**
- 0–20: No circularity programs. No packaging transparency. No end-of-life consideration.
- 21–40: Basic recycling messaging. Minimal take-back options. Standard packaging.
- 41–60: Active take-back program. Some packaging improvements. Circularity goals stated.
- 61–80: Comprehensive circularity strategy. Resale/repair programs. Reduced/recyclable packaging. Measurable progress on waste.
- 81–100: Circular business model. Design for disassembly. Closed-loop systems. Industry leadership on textile waste.

## Overall Grading

The overall score is a weighted average of the four dimension scores:

```
Overall = (WHERE × 0.25) + (WHO × 0.30) + (WHAT × 0.25) + (AFTER × 0.20)
```

| Score Range | Grade | Label |
|-------------|-------|-------|
| 80–100 | A | Leading |
| 65–79 | B | Good Progress |
| 50–64 | C | Getting Started |
| 35–49 | D | Needs Work |
| 0–34 | F | Failing |

## Red Flag Overrides

Certain conditions trigger an automatic grade cap or downgrade regardless of calculated score:

| Red Flag | Effect |
|----------|--------|
| Active OSHA serious/willful violations (past 2 years) | WHO dimension capped at D |
| FTC greenwashing settlement (past 3 years) | Overall grade capped at C |
| Confirmed child labor in supply chain | Overall grade capped at F |
| Confirmed forced labor in supply chain | Overall grade capped at F |
| Active EPA criminal enforcement | WHAT dimension capped at D |
| Repeated DOL wage theft violations | WHO dimension capped at D |

## Confidence Scoring

Each brand rating includes a confidence indicator based on data completeness:

- **High confidence**: 70%+ of indicators have data from verified sources
- **Medium confidence**: 40–69% of indicators have data
- **Low confidence**: Under 40% of indicators have data

Low-confidence ratings are clearly labeled. Brands can improve confidence by completing the voluntary ThreadGrade questionnaire or improving their public disclosures.

## Size Differentiation

Following Good On You's approach (and common sense), large brands face more demanding standards than small brands. A company with $1B+ in revenue and global supply chains is held to higher expectations on transparency and practices than a 10-person domestic operation.

Thresholds:
- **Large**: $50M+ annual revenue or parent company is publicly traded
- **Small**: Under $50M annual revenue and independently owned

Small brands cannot receive an F rating solely due to lack of disclosure (they may simply lack resources for comprehensive reporting). They can still receive F for active violations.

## Methodology Updates

This methodology is versioned and public. Changes are documented in the changelog with rationale. Major methodology changes trigger a re-rating of all brands within 30 days.

Current version: **1.0 (March 2026)**
