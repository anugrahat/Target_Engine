PYTHON ?= python3
PYTHONPATH_RUN = PYTHONPATH=packages/py

.PHONY: validate
validate:
	ruby scripts/validate_benchmark_packs.rb
	ruby scripts/validate_subset_configs.rb
	ruby scripts/validate_contract_examples.rb
	ruby scripts/validate_transcriptomics_fixtures.rb
	ruby scripts/generate_first_wave_registry.rb
	ruby scripts/validate_registry_artifacts.rb

.PHONY: test
test:
	$(PYTHONPATH_RUN) $(PYTHON) -m unittest discover -s tests/unit -p 'test_*.py'

.PHONY: registry-summary
registry-summary:
	$(PYTHONPATH_RUN) $(PYTHON) -m prioritx_data.cli

.PHONY: contrast-readiness
contrast-readiness:
	$(PYTHONPATH_RUN) $(PYTHON) -m prioritx_rank.cli

.PHONY: api-dev
api-dev:
	$(PYTHONPATH_RUN) $(PYTHON) apps/api/server.py
