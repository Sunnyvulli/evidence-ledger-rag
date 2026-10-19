.PHONY: run test eval serve format-check
run:
	python -m ledger.cli ingest
	python -m ledger.cli query
	python -m ledger.evaluate
test:
	python -m unittest discover -s tests -v
eval:
	python -m ledger.evaluate
serve:
	python -m ledger.service
format-check:
	python -m black --check ledger tests
