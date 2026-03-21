# Build Plan

## Phase 1: Foundation (Months 1–3)

**Goal:** Launch an MVP with 200 rated brands, a searchable directory, and 10 pieces of launch content.

### Month 1: Methodology + Data Pipeline

- [ ] Finalize scoring methodology with 3–5 expert reviewers (sustainable fashion, labor rights, environmental science)
- [ ] Set up PostgreSQL database with brand data schema
- [ ] Build OSHA API connector (first data pipeline component)
- [ ] Build sustainability report parser using Claude API
- [ ] Create brand seeding script (top 200 US brands by market share)
- [ ] Set up Next.js project with Tailwind, deploy to Vercel
- [ ] Domain registration and DNS setup

### Month 2: Brand Scoring + Frontend

- [ ] Process first 200 brands through the scoring pipeline
- [ ] Human review of initial batch (spot-check LLM outputs, calibrate scoring)
- [ ] Build brand directory page (searchable, filterable)
- [ ] Build individual brand report card pages
- [ ] Build "Better At Your Budget" price tier filter
- [ ] Build compare tool (side-by-side)
- [ ] Build methodology page
- [ ] Integrate Typesense/Meilisearch for search
- [ ] Set up OAR API connector
- [ ] Set up FTC case scraper

### Month 3: Content + Launch

- [ ] Write 5 brand report card articles ("Is [Brand] Ethical?")
- [ ] Write 3 "Better At Your Budget" guides
- [ ] Write 2 system stories ("Why Your $8 Tee Actually Costs $32" style)
- [ ] Beta test with FinMango ambassador network
- [ ] Iterate based on beta feedback
- [ ] Soft launch
- [ ] Set up monitoring/analytics (Plausible or similar, privacy-friendly)
- [ ] Social media presence (at minimum: Instagram, TikTok placeholder)

### Phase 1 Success Metrics

- 200 brands rated with at least medium confidence
- Site live and functional (directory, report cards, search, compare, budget filter)
- 10 pieces of launch content published
- Beta feedback from 20+ ambassador testers
- At least 1 brand report card ranking on page 1 for "[brand] ethical" query

---

## Phase 2: Growth (Months 4–8)

**Goal:** Expand to 1,000+ brands, launch content flywheel, begin B2B conversations.

### Brand Coverage Expansion (Months 4–6)
- [ ] Scale to 500 brands (Month 4), 750 (Month 5), 1,000+ (Month 6)
- [ ] Prioritize by US search volume and market share
- [ ] Add remaining data pipeline connectors (EPA, SEC, DOL, Customs)
- [ ] Automate re-scoring on data changes (monitoring layer)
- [ ] Launch voluntary brand questionnaire for self-reported data
- [ ] Begin brand outreach for questionnaire participation

### Content Flywheel (Months 4–8)
- [ ] 2–3 articles per week publishing cadence
- [ ] SEO-optimize for "[brand] ethical" and "sustainable [category] affordable" queries
- [ ] Launch email newsletter (weekly digest)
- [ ] Activate ambassador content creation (ThreadGrade-branded posts)
- [ ] University partnership outreach (UVA SEED model — student research teams)

### Product Development (Months 5–8)
- [ ] Browser extension prototype (Chrome)
- [ ] Mobile-responsive improvements
- [ ] User accounts (save favorites, set budget preferences)
- [ ] "Closet Audit" concept prototype

### Business Development (Months 6–8)
- [ ] Identify and approach 5–10 potential B2B partners (fintech, retail platforms)
- [ ] Apply for 3+ relevant grants
- [ ] Explore affiliate partnerships with higher-rated brands
- [ ] Draft API documentation for B2B licensing

### Phase 2 Success Metrics

- 1,000+ brands rated
- 50+ pieces of content published
- 10,000+ monthly site visitors
- Email list of 1,000+ subscribers
- Browser extension in beta
- At least 1 grant application submitted
- 3+ B2B conversations initiated

---

## Phase 3: Scale (Months 9–12+)

**Goal:** Establish ThreadGrade as the go-to US ethical fashion rating source. Sustainable revenue.

### Brand Coverage
- [ ] 5,000+ brands rated
- [ ] Full coverage of top 50 US retailers' private labels
- [ ] Quarterly comprehensive re-rating cycle
- [ ] Brand self-service portal for questionnaire submission

### Product
- [ ] Browser extension public launch
- [ ] Mobile app or PWA
- [ ] B2B API launch with documentation and pricing
- [ ] Retailer scorecards (aggregate ratings for where you shop)
- [ ] Interactive supply chain maps

### Content & Community
- [ ] Annual "State of American Ethical Fashion" data report
- [ ] Interactive Mango Stories modules for ThreadGrade
- [ ] Partner with 3+ university research programs
- [ ] ThreadGrade ambassador cohort (separate from FinMango)

### Revenue
- [ ] B2B data licensing generating revenue
- [ ] Brand transparency membership program live
- [ ] Affiliate revenue from ethical brand referrals
- [ ] Grant funding sustaining operations

### Phase 3 Success Metrics

- 5,000+ brands rated
- 100,000+ monthly site visitors
- Annual revenue covering operational costs
- Recognized as authoritative source by at least 2 major media outlets
- 3+ B2B licensing customers
- Annual data report generating press coverage

---

## Key Risks Per Phase

| Phase | Primary Risk | Mitigation |
|-------|-------------|-----------|
| 1 | Data quality — AI-parsed scores may be inaccurate | Human review of all initial ratings. Start with high-confidence data sources. Be transparent about limitations. |
| 1 | Scope creep — trying to rate too many brands too fast | Hard cap at 200 for launch. Prioritize quality over coverage. |
| 2 | Content bottleneck — can't sustain publishing pace | Activate ambassadors and university partners for content. Templatize report card articles. |
| 2 | Brand legal pushback | Proactive legal review. Only cite public data. Factual language, not opinion. |
| 3 | Revenue — grants dry up before B2B materializes | Start B2B conversations early (Phase 2). Keep costs lean. Affiliate revenue as bridge. |
| 3 | Competition — Good On You or new entrant targets US market | Move fast on mass-market coverage (private labels, discount brands). Community/data moat is hard to replicate. |
