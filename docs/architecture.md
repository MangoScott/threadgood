# Technical Architecture

## Overview

ThreadGrade is a web-first platform with an AI-powered data pipeline that continuously ingests, analyzes, and scores public data about US clothing brands. The architecture is designed for a lean nonprofit team to build and maintain.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CONSUMER LAYER                        │
│                                                          │
│   Next.js App (Vercel)                                   │
│   ├── Brand Directory (static generation)                │
│   ├── Brand Report Cards                                 │
│   ├── "Better At Your Budget" Search                     │
│   ├── Compare Tool                                       │
│   ├── Blog/Content (MDX)                                 │
│   └── API Routes (or standalone FastAPI)                 │
│                                                          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA LAYER                             │
│                                                          │
│   PostgreSQL (Railway/Fly)                               │
│   ├── brands                                             │
│   ├── scores (per-dimension, historical)                 │
│   ├── data_sources (raw ingested data)                   │
│   ├── indicators (structured, per-brand)                 │
│   ├── certifications                                     │
│   ├── red_flags                                          │
│   └── categories / price_tiers                           │
│                                                          │
│   Typesense/Meilisearch (search index)                   │
│                                                          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 AI PIPELINE LAYER                         │
│                 (Python, scheduled jobs)                  │
│                                                          │
│   Layer 1: INGESTION                                     │
│   ├── OSHA API connector                                 │
│   ├── EPA ECHO/TRI connector                             │
│   ├── FTC case scraper                                   │
│   ├── SEC EDGAR connector                                │
│   ├── OAR API connector                                  │
│   ├── Brand report scraper/parser                        │
│   ├── DOL WHD connector                                  │
│   └── News/press monitoring                              │
│                                                          │
│   Layer 2: ANALYSIS                                      │
│   ├── Claude API (document parsing)                      │
│   ├── Greenwashing detection (NLP)                       │
│   ├── Structured indicator extraction                    │
│   └── Cross-reference validation                         │
│                                                          │
│   Layer 3: SCORING                                       │
│   ├── Per-dimension scoring engine                       │
│   ├── Weighted average calculation                       │
│   ├── Red flag override system                           │
│   ├── Confidence interval calculation                    │
│   └── Grade assignment                                   │
│                                                          │
│   Layer 4: MONITORING                                    │
│   ├── New filing/violation watcher                       │
│   ├── Certification change detector                      │
│   ├── News alert processor                               │
│   └── Re-scoring trigger                                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack Details

### Frontend: Next.js + Tailwind CSS

**Why Next.js:**
- Static site generation (SSG) for brand pages means fast loads and great SEO. Each brand page is pre-rendered at build time.
- API routes handle dynamic functionality (search, compare) without a separate backend.
- React ecosystem is well-supported and FinMango has existing experience.
- Vercel deployment is essentially free at the expected traffic levels.

**Key pages:**
- `/` — Homepage with search, featured ratings, latest content
- `/brands` — Searchable/filterable brand directory
- `/brands/[slug]` — Individual brand report card
- `/compare` — Side-by-side brand comparison
- `/methodology` — Full methodology explanation
- `/blog` — Content (MDX-based)
- `/budget/[tier]` — "Better At Your Budget" filtered views

**Search:**
- Typesense or Meilisearch for the brand directory search
- Typo-tolerant, fast, filterable by category/price tier/grade
- Self-hostable, no vendor lock-in

### Database: PostgreSQL + Prisma

**Why PostgreSQL:**
- Relational data (brands, scores, sources, categories) fits SQL naturally
- JSONB columns for semi-structured data (raw API responses, parsed indicators)
- Strong ecosystem, easy to host on Railway or Fly.io

**Core schema (simplified):**

```sql
-- Brands
brands
  id              UUID PRIMARY KEY
  name            TEXT NOT NULL
  slug            TEXT UNIQUE NOT NULL
  parent_company  TEXT
  website         TEXT
  price_tier      ENUM('$', '$$', '$$$', '$$$$')
  annual_revenue  TEXT -- range bucket
  is_large        BOOLEAN
  logo_url        TEXT
  created_at      TIMESTAMP
  updated_at      TIMESTAMP

-- Categories (many-to-many with brands)
categories
  id              UUID PRIMARY KEY
  name            TEXT NOT NULL
  slug            TEXT UNIQUE NOT NULL

brand_categories
  brand_id        UUID REFERENCES brands
  category_id     UUID REFERENCES categories

-- Scores (historical, one row per scoring event)
scores
  id              UUID PRIMARY KEY
  brand_id        UUID REFERENCES brands
  scored_at       TIMESTAMP
  where_score     DECIMAL(5,2)
  who_score       DECIMAL(5,2)
  what_score      DECIMAL(5,2)
  after_score     DECIMAL(5,2)
  overall_score   DECIMAL(5,2)
  grade           ENUM('A', 'B', 'C', 'D', 'F')
  confidence      ENUM('high', 'medium', 'low')
  is_current      BOOLEAN DEFAULT true
  methodology_version TEXT

-- Data source records (raw ingested data)
data_sources
  id              UUID PRIMARY KEY
  brand_id        UUID REFERENCES brands
  source_type     TEXT NOT NULL -- 'osha', 'epa', 'ftc', 'sec', 'brand_report', etc.
  source_url      TEXT
  raw_data        JSONB
  ingested_at     TIMESTAMP
  processed       BOOLEAN DEFAULT false

-- Structured indicators (extracted from data sources)
indicators
  id              UUID PRIMARY KEY
  brand_id        UUID REFERENCES brands
  dimension       ENUM('where', 'who', 'what', 'after')
  indicator_name  TEXT NOT NULL
  value           JSONB -- flexible: boolean, number, text, etc.
  source_id       UUID REFERENCES data_sources
  extracted_at    TIMESTAMP

-- Red flags
red_flags
  id              UUID PRIMARY KEY
  brand_id        UUID REFERENCES brands
  flag_type       TEXT NOT NULL
  description     TEXT
  source_id       UUID REFERENCES data_sources
  active          BOOLEAN DEFAULT true
  detected_at     TIMESTAMP
  resolved_at     TIMESTAMP

-- Certifications
certifications
  id              UUID PRIMARY KEY
  brand_id        UUID REFERENCES brands
  cert_name       TEXT NOT NULL
  cert_body       TEXT
  valid_from      DATE
  valid_to        DATE
  verified        BOOLEAN DEFAULT false
  source_url      TEXT
```

### AI / LLM Layer: Anthropic Claude API

**Model selection:**
- **Claude Sonnet** for document parsing (sustainability reports, legal filings, news articles). Best balance of quality and cost for complex extraction.
- **Claude Haiku** for classification tasks (greenwashing detection, indicator categorization). Fast and cheap for high-volume processing.

**Key LLM tasks:**
1. **Sustainability report parsing**: Extract structured indicators from PDF/HTML reports. Output: JSON with indicator name, value, confidence, page reference.
2. **Greenwashing detection**: Score language in brand communications on a vagueness/specificity scale. Flag unverifiable claims.
3. **News processing**: Extract relevant facts from news articles about brand labor/environmental incidents.
4. **Cross-reference validation**: Compare brand claims against public data (e.g., "we've had no violations" vs. OSHA records).

**Prompt architecture:**
- System prompts define the extraction schema and scoring criteria
- Few-shot examples for each extraction type
- Structured JSON output for downstream processing
- Citation requirements (LLM must reference specific source text for each extracted indicator)

### Data Pipeline: Python

**Orchestration:** Cron jobs for MVP, migrate to Temporal.io or Prefect if complexity warrants it.

**Schedule:**
- Daily: OSHA, FTC, news monitoring
- Weekly: OAR, DOL
- Monthly: Full brand report re-processing
- Quarterly: SEC filings, comprehensive re-scoring
- On-demand: Triggered by monitoring layer alerts

**Key libraries:**
- `httpx` / `requests` — API calls
- `beautifulsoup4` / `scrapy` — Web scraping
- `anthropic` — Claude API client
- `pdfplumber` / `pymupdf` — PDF text extraction
- `pandas` — Data processing
- `sqlalchemy` / `prisma-client-py` — Database access

### Hosting

| Service | Purpose | Estimated Cost |
|---------|---------|---------------|
| Vercel (free tier) | Next.js frontend | $0/mo |
| Railway or Fly.io | PostgreSQL, data pipeline, search index | $20-50/mo |
| Anthropic API | LLM processing | $500-2000/mo (volume dependent) |
| GitHub Actions | CI/CD, scheduled pipeline runs | $0 (free tier) |

## MVP Implementation Order

1. **Database schema** — Set up PostgreSQL, create tables, seed with 200 brand stubs
2. **OSHA data connector** — First pipeline component, free API, immediate value
3. **Brand report parser** — LLM-based extraction from sustainability reports
4. **Scoring engine** — Apply methodology to available data, output grades
5. **Next.js brand directory** — Searchable list of rated brands
6. **Brand report card page** — Individual brand detail pages
7. **Search integration** — Typesense/Meilisearch for directory search
8. **"Better At Your Budget" filter** — Price tier filtering on directory
9. **Compare tool** — Side-by-side brand comparison
10. **Content/blog** — MDX-based blog for launch articles

## Future Architecture Considerations

- **Browser extension**: Chrome/Firefox extension that queries the ThreadGrade API when visiting retail sites. Shows inline grade badges.
- **API layer**: RESTful API for B2B licensing. Rate limiting, API keys, usage tracking.
- **Webhook system**: Notify B2B partners when brand ratings change.
- **Worker queue**: As pipeline complexity grows, move from cron to a proper job queue (Bull, Celery) for better retry/monitoring.
