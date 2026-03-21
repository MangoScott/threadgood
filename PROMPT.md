# ThreadGrade — AI Build Prompt

Copy and paste the prompt below into a new Claude conversation (or similar LLM) to continue building ThreadGrade. Replace `[INSERT YOUR SPECIFIC REQUEST HERE]` with what you need.

---

## The Prompt

```
You are helping me build ThreadGrade, an AI-powered ethical fashion rating platform for American shoppers. It is a project of FinMango, a 501(c)(3) nonprofit focused on financial health (finmango.org).

Context:
- ThreadGrade rates US clothing brands on a letter-grade scale (A through F) across four dimensions: WHERE (supply chain transparency/geography), WHO (labor practices/worker welfare), WHAT (materials/chemicals/durability), and AFTER (circularity/end-of-life).
- The core differentiator is an "affordability layer" — ratings are organized by price tier ($, $$, $$$, $$$$) so users can find the best ethical option at their actual budget.
- We leverage US-specific public data sources as a competitive moat: US Customs import records, OSHA workplace safety violations, EPA enforcement data, FTC greenwashing complaints, SEC ESG disclosures, CA Supply Chain Transparency Act filings, DOL Wage & Hour data, and the Open Apparel Registry.
- The AI data pipeline has four layers: (1) Ingestion — automated scrapers/API connectors pulling from public sources on schedule, (2) Analysis — LLMs parse unstructured data into structured indicators, flag greenwashing, (3) Scoring — algorithmic engine applies methodology and outputs grades with confidence intervals, (4) Monitoring — continuous watch for new filings/violations/news that trigger re-scoring.
- Scoring weights: WHERE 25%, WHO 30%, WHAT 25%, AFTER 20%. Red-flag system overrides calculated grade downward for serious violations.
- Tech stack: Next.js + Tailwind (frontend), PostgreSQL + Prisma (database), Claude API via Anthropic (LLM layer), Python (data pipeline), Typesense or Meilisearch (search), Vercel + Railway/Fly (hosting).
- Target: MVP with 200 rated brands, searchable directory, brand report cards, "Better At Your Budget" search, and compare tool.
- Voice/tone: Direct, data-driven, no-BS. Not preachy. Financial health framing — meet people where they are, don't shame them for shopping at Walmart.

What I need help with right now: [INSERT YOUR SPECIFIC REQUEST HERE — e.g., "Build the database schema for the brand data model", "Write the scoring algorithm", "Create the Next.js brand directory page", "Draft the first brand report card for Nike", "Build the OSHA data scraper", "Design the homepage", etc.]

Design preferences: I prefer bold simplicity, hand-drawn aesthetic touches (Caveat + DM Sans fonts), green palette, conversational data-driven copy. Avoid corporate polish and AI-sounding language (no em dashes, no filler).
```

---

## Example Requests

Here are some specific things you might ask for:

### Data Pipeline
- "Build the OSHA API connector in Python that pulls violation data for a given employer name and outputs structured JSON"
- "Write the sustainability report parser that uses Claude API to extract structured indicators from a brand's PDF report"
- "Create the scoring engine that takes a brand's indicators and outputs per-dimension scores and an overall grade"
- "Build the greenwashing detection prompt that scores brand language on a vagueness scale"

### Frontend
- "Create the Next.js brand directory page with search, category filter, price tier filter, and grade filter"
- "Build the brand report card component showing overall grade, per-dimension breakdown, data sources, and price tier"
- "Design the homepage with search bar, featured ratings, and latest content"
- "Build the side-by-side brand comparison tool"

### Database
- "Create the Prisma schema for the full ThreadGrade data model"
- "Write the brand seeding script that populates the database with the top 200 US clothing brands"

### Content
- "Draft the first brand report card article for Nike in ThreadGrade's voice"
- "Write a 'Better At Your Budget' guide for ethical basics under $25"
- "Draft the methodology page copy explaining how ThreadGrade rates brands"

### Strategy
- "Help me identify the top 200 US clothing brands by market share to rate first"
- "Draft outreach emails for potential B2B data licensing partners"
- "Write a grant proposal narrative for ThreadGrade targeting Google.org"
