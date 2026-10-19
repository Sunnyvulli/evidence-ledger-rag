# Failures worth inspecting

## Lexical agreement hides changed meaning
The source says that a local workflow requires approval. A modified claim says it does not require approval. Most content words still overlap, so the deterministic support score stays below the review threshold. Another claim changes a warning about factual correctness into a guarantee. Both are missed. The retained six-case probe suite contains five unsupported examples; only three are flagged. The regression test intentionally preserves one such failure so an implementation edit cannot silently erase this known limitation from the report.

This rules out treating low risk as factual verification. Independent contradiction labels, a validated semantic comparator and separate threshold calibration would be needed before expanding that claim.

## Hybrid retrieval is not automatically better
BM25 finds the expected file in 10 of 14 top-three chunk sets. Character TF-IDF and RRF each find it in 11. Hybrid MRR is 0.631 versus 0.619 for the character baseline on this run, but only 14 author-written queries and one expected file per query are available. Three expected sources are missed, and several documents discuss overlapping topics. No significance, independent generalization or retrieval completeness claim follows.

## An instruction is still returned as a quotation
A document saying to ignore restrictions can be indexed and quoted. The engine has no executor or network/tool capability, and its read-only query leaves database bytes unchanged in the test. That establishes only this service's capability boundary. A separate consuming model could repeat or act on the quotation with other tools. No model-level injection success rate has been measured.

## Durable failure behavior
Injected chunk-insert failure rolls back changed documents/search content/signature; retry after removing the injected failure succeeds. Invalid UTF-8, oversized files, empty corpus and symlinks fail before content mutation. A missing query index returns 503 and is not created. An unavailable monitor sink also returns 503. These are controlled local tests; there is no production incident history or cloud-recovery claim.
