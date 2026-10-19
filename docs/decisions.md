# Decisions

## 1. Local operator documentation as the corpus
Use real, inspectable owner-authored project documentation and retain exact source commits/hashes. This makes the use case concrete without redistributing external paper text or private employer information. Ten closely related documents and authored query labels are development evidence, not diverse independent validation. Ingest only a trusted bounded directory; do not crawl arbitrary URLs.

## 2. Incremental identities, transactional replacement
Document SHA-256 determines change; chunk IDs bind path, source hash and ordinal. A failed replacement rolls back document rows, chunks, FTS content and the corpus signature together. Unchanged identities persist. FTS rows are rebuilt within a changed batch rather than maintaining a more complex trigger set. This costs a full search-index rewrite on changes; it is acceptable at the explicit 1 MB corpus limit. Input hashes identify captured bytes, not an adversarial storage guarantee. SQLite schema/metadata and the local operator are trusted.

## 3. Lexical baselines before model dependencies
SQLite FTS5 BM25 is combined with character 3–5-gram TF-IDF through reciprocal-rank fusion, using established k=60 with top-20 candidate lists. This is cheap to inspect and handles some spelling overlap; it does not supply semantic embeddings. Candidate lists may contain several chunks from one document. Evaluate top-three chunks with one expected file per query; do not mislabel this as distinct-document recall or a comprehensive relevance judgment. Tie-breaking uses stable chunk IDs. TF-IDF is refit per query, exposing rather than hiding its local cost.

References consulted 2026-10-19: [SQLite FTS5](https://www.sqlite.org/fts5.html) (lower BM25 scores rank better); [scikit-learn TfidfVectorizer](https://scikit-learn.org/1.8/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html); [Cormack et al., 2009](https://doi.org/10.1145/1571941.1572114). RRF is not an original algorithm and its paper does not guarantee improvement on this corpus.

## 4. Extractive answer provenance and a separate review signal
Return up to two relevant sentences with chunk ID, source hash and exact supporting chunk text. Fixed lexical overlap/similarity heuristics can abstain but are not calibrated confidence. Span equality is provable by construction; it does not establish that the source is true, current, complete or responsive to the question. Apply the existing deterministic lexical support guard as a transparent baseline, with retained negation/meaning failures. Do not transplant learned research scores, claim factual verification, or invoke paid model APIs.

## 5. Loopback service and bounded HTTP contract
Only health and read-only query operations are exposed on loopback. Indexing is a separate CLI operator action. Validate query length, method, strict k and body size, open SQLite read-only, and retain only query hashes in monitoring. A monitor failure returns 503 instead of silently losing the event. This is local development isolation, not remote identity, immutable auditing, service-rate limiting or production authentication. No public backend deployment is claimed.
