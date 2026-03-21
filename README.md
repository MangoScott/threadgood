[README-threadgrade.md](https://github.com/user-attachments/files/26161213/README-threadgrade.md)
# ThreadGrade

**An AI-powered ethical fashion rating platform for American shoppers.**

A [FinMango](https://finmango.org) initiative (501(c)(3))

---

## The Problem

Ethical fashion platforms today mirror the financial literacy problem: they give consumers information and assume behavior will change. But information without access is just guilt.

Telling a Walmart shopper to buy from Patagonia isn't ethical fashion guidance. It's privilege dressed up as advice.

## What ThreadGrade Does

ThreadGrade rates US clothing brands on a **letter-grade scale (A through F)** across four dimensions, then layers in something nobody else does: **price tiers**. So instead of "here are 50 A-rated brands you can't afford," you get:

> "What's the best C+ or above I can buy for under $30 in basics?"

### The Four Dimensions

| Dimension | What It Measures |
|-----------|-----------------|
| **WHERE** | Supply chain transparency and geography. Where are garments made? How much of the chain is disclosed? |
| **WHO** | Labor practices and worker welfare. Living wages, safety records, union rights, child/forced labor risk. |
| **WHAT** | Materials, chemicals, and durability. What fibers are used? Chemical safety? Expected garment lifespan? |
| **AFTER** | End-of-life and circularity. Recyclability, take-back programs, resale infrastructure, packaging waste. |

### Price Tiers

| Tier | Range | Examples |
|------|-------|---------|
| $ | Under $25/item | Walmart, Amazon Essentials, Shein, Old Navy |
| $$ | $25–$75/item | Target (All in Motion, Goodfellow), H&M, Uniqlo, Gap |
| $$$ | $75–$150/item | Everlane, Madewell, Levi's premium |
| $$$$ | $150+/item | Patagonia, Eileen Fisher, Reformation |

## Why This Exists

Good On You (Australia) built a global brand rating system. It's good. But it has gaps for Americans:

- **Mass-market blind spot**: Private labels at Target, Walmart, Amazon, Costco are often unrated
- **Price-agnostic**: Recommending $150 ethical tees to someone shopping at Old Navy is tone-deaf
- **Global methodology**: Doesn't leverage US-specific public data (Customs, OSHA, EPA, FTC, SEC)
- **Manual analysis**: Human analysts create bottlenecks and staleness
- **Aspirational tone**: Assumes shoppers have unlimited choice and budget

ThreadGrade is built for how Americans actually shop.

## The US Data Moat

The structural advantage of a US-focused platform is access to public data that global competitors don't fully leverage:

| Source | What It Provides |
|--------|-----------------|
| US Customs & Border Protection | Importer name, country of origin, supplier factories |
| OSHA | Workplace safety inspections, violations, penalties |
| EPA (ECHO + TRI) | Environmental enforcement, chemical releases |
| FTC | Greenwashing complaints, textile labeling violations |
| SEC EDGAR | ESG disclosures for publicly traded companies |
| CA SB 657 | Supply chain slavery/trafficking disclosures |
| DOL Wage & Hour | Minimum wage and overtime violations |
| Open Apparel Registry | Verified factory-to-brand connections |

See [docs/data-sources.md](docs/data-sources.md) for full details and access methods.

## Technical Architecture

Four-layer AI pipeline:

1. **Ingestion** — Automated scrapers and API connectors pull from public data sources on schedule. Raw data normalized into a unified brand-data schema.
2. **Analysis** — LLMs parse unstructured data (sustainability reports, press releases, legal filings) into structured indicators. NLP flags greenwashing language patterns.
3. **Scoring** — Algorithmic engine applies methodology, outputs per-dimension scores and overall grades with confidence intervals.
4. **Monitoring** — Continuous watch for new filings, violations, news. Triggers re-scoring when material changes detected.

See [docs/architecture.md](docs/architecture.md) for the full tech stack and implementation details.

## Scoring

Each dimension receives a score from 0–100. The overall grade is a weighted average:

- **WHERE**: 25% (transparency is foundational)
- **WHO**: 30% (labor practices are highest-impact)
- **WHAT**: 25% (materials drive environmental impact)
- **AFTER**: 20% (circularity is important but still emerging)

A "red flag" system overrides calculated grades downward for serious violations (active OSHA fines, FTC greenwashing settlements, confirmed child labor).

| Grade | Label | Meaning |
|-------|-------|---------|
| A | Leading | Industry leadership. High transparency, strong practices, third-party verified. |
| B | Good Progress | Meaningful policies in place. Transparent on most issues. Measurable improvements. |
| C | Getting Started | Some transparency and good practices, but significant gaps remain. |
| D | Needs Work | Minimal transparency. Few concrete practices. Claims without verification. |
| F | Failing | No meaningful transparency. Potential active harm (violations, fines, lawsuits). |

See [docs/methodology.md](docs/methodology.md) for the full scoring breakdown.

## Roadmap

### Phase 1: Foundation (Months 1–3)
Launch MVP with 200 rated brands, searchable directory, and launch content.

### Phase 2: Growth (Months 4–8)
Scale to 1,000+ brands, launch content flywheel, browser extension prototype, begin B2B conversations.

### Phase 3: Scale (Months 9–12+)
5,000+ brands, B2B API and data licensing, mobile app, annual "State of American Ethical Fashion" report.

See [docs/build-plan.md](docs/build-plan.md) for the detailed phased plan.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (React) + Tailwind CSS |
| Backend | Next.js API routes or FastAPI (Python) |
| Database | PostgreSQL + Prisma ORM |
| AI / LLM | Anthropic Claude API |
| Data Pipeline | Python (scheduled jobs) |
| Search | Typesense or Meilisearch |
| Hosting | Vercel (frontend) + Railway or Fly.io (backend/DB) |

## Building With AI

This repo includes a pre-built prompt for continuing development with Claude or similar LLMs. See [PROMPT.md](PROMPT.md).

## About FinMango

[FinMango](https://finmango.org) is a 501(c)(3) nonprofit focused on financial health — not just financial literacy. We've reached 1M+ people across 13+ countries with research partnerships including Google Health, WHO, World Bank, and IMF.

Our core thesis: financial education only works when people are already financially stable. ThreadGrade applies the same logic to ethical fashion — information only helps when people have real choices.

## License

This project is open source under the [MIT License](LICENSE).

## Contributing

ThreadGrade is in early development. If you're interested in contributing — especially around data pipeline development, scoring methodology, or content — open an issue or reach out.
