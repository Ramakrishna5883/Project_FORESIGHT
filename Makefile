.PHONY: run-pipeline run-dashboard run-api test clean

PYTHON = python

run-pipeline:
	$(PYTHON) run_pipeline.py

run-dashboard:
	$(PYTHON) run_dashboard.py

run-api:
	$(PYTHON) run_api.py

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

clean:
	rm -rf __pycache__ */__pycache__ database/foresight.db data/processed/* data/reports/* models/*.pkl
