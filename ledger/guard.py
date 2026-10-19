"""Dependency-free adaptation of the owner's research lexical triage baseline.

This is a review signal, not entailment or factual verification.
"""

import re

STOP = set(
    "the a an is are was were of in on to for and or by with as from that this it its be has have had at".split()
)


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", re.sub(r"\[\d+\]", "", text.lower()))) - STOP


def triage(claim, citations):
    evidence = " ".join(c["text"] for c in citations)
    ct, et = tokens(claim), tokens(evidence)
    coverage = len(ct & et) / max(len(ct), 1)
    nums = lambda text: set(re.findall(r"\b\d+(?:\.\d+)?\b", text))
    numbers = nums(re.sub(r"\[\d+\]", "", claim))
    unmatched = len(numbers - nums(evidence)) / max(len(numbers), 1)
    risk = max(1 - coverage, unmatched, float(not citations))
    return {
        "risk": risk,
        "review_required": risk >= 0.5,
        "warning": "Lexical triage can miss contradictions and semantic changes.",
    }
