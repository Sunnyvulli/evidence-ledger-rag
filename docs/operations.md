# Operator guide

Install the pinned requirements in a Python 3.12 environment, then `make run` for an index/query/evaluation. It writes only `.local/` runtime state and `results/evaluation.json`; repeated ingestion is a no-op if the captured document hashes agree. `make test` runs real loopback HTTP and storage failure checks. Query logs contain hashes and timings, not raw queries; local OS permissions still matter.

`python -m ledger.cli ingest --corpus /absolute/path/to/markdown --database .local/custom.sqlite` explicitly replaces the corpus snapshot in that index. Removal from a nonempty source directory removes a document. An empty directory is rejected; there is no HTTP indexing route. Keep original files under version control and do not put secrets in the corpus. A local owner can edit trusted files, hashes and database metadata.

`python -m ledger.service --database .local/custom.sqlite --monitor .local/monitor.jsonl` binds to loopback port 8090. `/health` returns 503 for a missing index; `/query` validates bounds and returns 400 for invalid input, 404 for unknown endpoints, or 503 for storage/monitor failure. No remote authorization is present. Do not publish the backend as an unauthenticated network service.

The recorded results explorer is static and can be served with GitHub Pages. It reads the checked-in evaluation JSON, never sends user queries to a backend and cannot run ingestion. Published raw results refer to the recorded source hashes, versions and the explicit authored-query set. CI re-executes the evaluator and uploads that run separately; timings may differ.
