# Evidence-support guard provenance

The deterministic triage rule adapts Hanumantha Rao Vulli's existing `research-suite/src/research_suite/checkpoints.py` in [Data-Engineer_AI](https://github.com/Sunnyvulli/Data-Engineer_AI). The source Git blob SHA is `c3c8ef8ce328a3ae7f4c037cc2ea6d5e2b807093`, verified from the retained source file. The source's `tokens`, feature calculation and `triage` rule use `max(1 - token coverage, unmatched-number fraction, missing-citation indicator)` and threshold 0.5. This project rewrites that small rule without numpy/pandas/model loading and retains the same stopword set and number convention.

The research repository also evaluates learned models and external datasets. **None of those learned weights or external performance figures are inherited here.** This service evaluates only six designed probes against the deterministic rule. Its 0.60 unsupported-case recall belongs to these five unsupported examples; it is not RAGTruth performance, an entailment score, or a general confidence estimate.

The exact-span answer path usually scores low risk because it copies its own citation. That is a provenance check, not an independent guardrail against source errors. Controlled altered-claim probes are evaluated separately and expose semantic/negation misses. No paper acceptance or novel detection algorithm is claimed.
