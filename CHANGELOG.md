# Changelog

## 0.1.0 candidate - 2026-10-19
- Added bounded transactional Markdown ingestion, stable unchanged chunk identities, deletion/replacement, and source/corpus hashes.
- Added BM25/character TF-IDF/RRF baselines, cited extracts, explicit abstention heuristics and lexical support review.
- Executed 14 authored queries and six controlled guard probes; retained missed files and semantic failures, environment versions, timings and hashes.
- Added actual loopback JSON/monitoring behavior, 16 behavioral tests, formatter, full-history scan CI and static recorded-results explorer.

A release/tag is pending CI and the explicit release milestone. No AWS/model-generation/public-backend deployment is claimed.

## Unreleased extraction fix - 2026-10-19
- Browser review reproduced an exact-but-unresponsive audit-sink answer.
- Added question-term rarity/length scoring across retrieved chunks and a relative secondary-extract threshold.
- Two before-failing regressions bring the suite to 18 tests; retained initial/revised outputs and development-tuning limits. Retrieval scores and guard failures remain unchanged.
