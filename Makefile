PYTHON ?= python

.PHONY: atlas test validate

atlas:
	$(PYTHON) scripts/build_public_atlas_data.py

test:
	$(PYTHON) -m unittest discover -s tests -v

validate: atlas test
	$(PYTHON) -m compileall -q scripts tests
