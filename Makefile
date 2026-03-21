.PHONY: osha oar reports fti ktc cbp goy certs score build all clean

PYTHON := python3

# Step 1: Scrape OSHA enforcement data
osha:
	$(PYTHON) scripts/scrape_osha.py

# Step 2: Scrape Open Supply Hub facility data (requires paid API)
oar:
	$(PYTHON) scripts/scrape_oar.py

# Step 3: Parse sustainability reports with Claude
reports:
	$(PYTHON) scripts/parse_reports.py

# Step 4: Load Fashion Transparency Index data
fti:
	$(PYTHON) scripts/load_fti.py

# Step 5: Load KnowTheChain benchmark data
ktc:
	$(PYTHON) scripts/load_ktc.py

# Step 6: Load CBP forced labor / WRO data
cbp:
	$(PYTHON) scripts/load_cbp.py

# Step 7: Scrape Good On You ratings
goy:
	$(PYTHON) scripts/scrape_goy.py

# Step 8: Load certifications data (B Corp, Fair Trade, etc.)
certs:
	$(PYTHON) scripts/load_certs.py

# Step 9: Run scoring engine
score:
	$(PYTHON) scripts/score.py

# Step 10: Generate site data
build:
	$(PYTHON) scripts/build_site_data.py

# Run everything in order (skipping paid APIs)
all: osha fti ktc cbp certs score build

# Run with all sources (including report parsing and OAR)
all-full: osha oar reports fti ktc cbp goy certs score build

# Delete all generated data
clean:
	rm -rf data/osha/*.json
	rm -rf data/oar/*.json
	rm -rf data/reports/*.json
	rm -rf data/fti/*.json
	rm -rf data/ktc/*.json
	rm -rf data/cbp/*.json
	rm -rf data/goy/*.json
	rm -rf data/certs/*.json
	rm -rf data/scores/*.json
	rm -rf data/site/brands.json
	rm -rf data/site/brands/*.json
	@echo "Cleaned all generated data."
