.PHONY: install test data-wid data-fixtures release clean lint

install:
	pip install -e ".[dev]"

test:
	pytest

# Fetch real WID bulk data (requires network access to wid.world)
# then build the v0.1 release.
data-wid:
	wga fetch wid
	wga build --out-dir data/release

# v0.2: HFCS data must be downloaded manually from the ECB Data Portal.
# `wga fetch hfcs` prints the schema and source URL if the file is missing.
data-hfcs:
	wga fetch hfcs
	wga build --out-dir data/release

# Build a release from the bundled fixtures (no network required).
data-fixtures:
	WGA_WID_LOCAL=data/fixtures wga build --out-dir data/release --version 0.1.0-fixtures

# Alias
release: data-wid

clean:
	rm -rf data/raw/wid/* data/interim/* data/release/*

lint:
	ruff check wealth_gini_atlas tests
