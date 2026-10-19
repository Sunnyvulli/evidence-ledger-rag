# Lab: reliable analytics from real observations

**Audience:** introductory SQL/Python learners. **Duration:** 60–90 minutes. **Prerequisites:** Python functions, basic SELECT/GROUP BY. This is a teaching sample, not a claim of prior teaching employment.

## Learning outcomes
By the end, learners should distinguish missing observations from zeros; reconcile aggregate counts; implement a repeat-safe batch; and recognize target leakage.

## 1. Prepare (10 minutes)
Clone the repository. In projects/mobility-quality run python pipeline.py and python -m unittest -v. Inspect data/SOURCE.md to identify the source, license, measurement period, and hash. Explain why real historical data are different from live operational evidence.

## 2. Inspect (15 minutes)
Run these SQLite queries using Python's sqlite3 module or your preferred SQLite client:

```sql
SELECT COUNT(*) AS rows, SUM(cnt) AS rentals FROM observations;
SELECT dteday, COUNT(*) AS hours, SUM(cnt) AS rentals
FROM observations GROUP BY dteday HAVING COUNT(*) < 24 ORDER BY dteday;
SELECT COUNT(*) AS mismatches FROM observations
WHERE cnt <> casual + registered;
```

Expected first result: 17,379 rows and 3,292,679 rentals. Expected mismatches: 0. The missing-hours query returns dates with incomplete hourly coverage; do not fill gaps with zero automatically.

## 3. Reason and implement (20 minutes)
1. Explain why cnt = casual + registered is stronger than cnt >= 0. (2 points)
2. Run the same file twice. Explain why the second run does not duplicate data. (2 points)
3. Create a temporary CSV with one invalid hour and one duplicate. Run validate and inspect rejection reasons. Preserve the original dataset. (3 points)
4. Modify a date-hour key without changing the ID. Which constraint still catches the duplicate? (2 points)
5. Explain why passing a corrupted row to a forecast model can matter even if the code does not crash. (1 point)

## 4. Evaluate (15 minutes)
Inspect model-summary.csv. Why must casual and registered not be available as predictors when estimating the same hour's cnt? Explain why the shuffled and chronological results cannot be interpreted as a controlled causal comparison. Distinguish retrospective estimation using observed weather from forecasting future demand. (5 points)

## Answer key and rubric
1. An incorrect non-negative total can still disagree with components; reconciliation enforces a domain relationship.
2. The SHA-256 plus active-snapshot manifest recognizes a repeat of the same batch; replacement is transactional rather than append-only.
3. The hour 25 violates the 0–23 range; a repeated valid key/ID violates uniqueness. Full credit requires checking the actual reason codes and avoiding edits to original input.
4. The immutable record ID still triggers duplicate_key. Domain rules and relational rules protect different invariants.
5. A plausible numeric value can shift aggregates or predictions silently.
6. casual + registered equals the target, so using them leaks the answer. Different time periods and distributions confound the split comparison. Observed same-hour weather would not be known exactly before that hour.

Total: 15 points. Award evaluation points for (a) leakage identity 2, (b) confounding/distribution caveat 2, (c) forecasting distinction 1. Partial credit requires a correct explanation, not just reproducing an output.

## Extension
Write a test showing that an invalid-schema batch preserves the previous database. Design, but do not claim to have deployed, a notification policy for a failed batch. Explain what evidence would be necessary to judge its usefulness.
