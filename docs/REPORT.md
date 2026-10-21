# Implementation and measurement report — 21 October 2026

The audit and prioritized plan were completed and reported before production edits;
see [AUDIT.md](AUDIT.md). Work stayed local. Nothing was deployed, published,
provisioned in the cloud, pushed, or submitted to the organizer.

## What changed

| Files | Change and purpose |
|---|---|
| `search.py` | Token/facet inverted postings, original-ID lookup, conservative constraint intersection, IDF field weights and phrase evidence, balanced mixed-choice ranking, and preordered exact catalog pages. |
| `query.py` (new) | Dataclass intent plans; budgets/ranges, source audiences, colors/patterns, product types, limited reviewed aliases/typos, per-choice requirements and complementary scope. Unknown residual terms require evidence. Unsupported size/stock/shipping/discount requests abstain. |
| `recommendations.py` (new) | Reviewed product-type compatibility, separate accessory constraints, per-item budgets, source-audience checks, deterministic ranking and current-page references. |
| `server.py` | Remove standalone GET from the MCP route: now returns the required 405 instead of opening SSE. SDK transport remains intact. |
| `tests/test_contract.py`, `test_index.py`, `test_query.py`, `test_ranking.py`, `test_recommendations.py`, `test_server.py` (new) | Validation, 240 exact-page combinations, inclusive bounds, nulls, leading zeros, retrieval equivalence, constraints/precedence, phrases, mixed coverage, pagination, complementary scope and HTTP routing. |
| `tests/test_search.py` | Replace the recommendation-stub-only assertion with current-page reference/ID checks; keep existing search assertions. |
| `evaluation/cases.json`, `run.py`, `mcp_check.py` (new) | Frozen development/held-out cases, independent exact-page oracle, catalog-rule relevance proxies, and real MCP concurrency measurements. |
| `evaluation/reports/*.json` (new) | Raw per-case IDs, measurements, intermediate results, baseline/final comparisons and source manifest. |
| `README.md`, `docs/AUDIT.md`, `docs/REPORT.md` | Setup, audit, architecture, measured results, limitations and next experiments. |
| `.gitignore`, `.dockerignore` | Exclude local audit scratch files and downloaded reference sources. |

Published schemas, tool name `search_products`, protocol revision `2025-11-25`,
requirements and Dockerfile are unchanged. There are no added runtime dependencies
or model/API requirements. Black 26.10.1 was used locally as a development formatter.
The original catalog SHA-256 was rechecked and is unchanged. Git with LFS disabled
shows materialized JSON versus its tracked pointer; do not commit that as a data edit.

## Measurements

The same workstation ran Linux/Python 3.12 containers with the original pinned
requirements. Native Python 3.14 tests also pass. These are local measurements,
not an organizer run, a prediction of Bedrock grades, or a claimed competition score.

| Check | Starter | Improved |
|---|---:|---:|
| Existing/new unit-test methods | 5/5 | 34/34 |
| Official public MCP smoke test | pass | pass |
| Standalone MCP GET with SSE Accept | 200 stream (contract failure) | 405 |
| Frozen development checks | 11/22 | 22/22 |
| Frozen held-out checks | 8/15 | 15/15 |
| All local checks after final constraint review | 19/37 across baseline splits | 37/37 |
| Ranking-area mean rule-proxy nDCG@10, dev | 0.4454 | 1.0000 |
| Ranking-area mean rule-proxy nDCG@10, held-out | 0.3112 | 1.0000 |
| Mixed-choice checks, combined splits | 0/5 | 5/5 |
| Recommendation checks, combined splits | 0/4 | 4/4 |
| Irrelevant/impossible examples correctly empty | 6/6 | 6/6 |
| Real MCP exact workload, correct / timed calls | 300/300 | 300/300 |
| Real MCP exact workload, median | 171.18 ms | 40.72 ms |
| Real MCP exact workload, nearest-rank p95 | 631.98 ms | 123.81 ms |
| Startup: load + index, dev run | 4.03 s | 5.58 s |
| Peak process RSS, dev run | 757.8 MiB | 643.6 MiB |

Final all-case rerun measured 6.36 s startup and 643.7 MiB peak process RSS. Startup
is slower, in exchange for more indexing and precomputed exact orders. These are
single diagnostic samples affected by CPU load and filesystem caches, not precise
startup distributions. A healthy improved server container used about 659 MiB in
a post-workload Docker snapshot; that is a different metric from process peak RSS.

For real MCP latency, both versions used the same localhost port, client, exact
oracle and pool checksum
`dc7b51d5ca0a9f8ec8316fc2dc543326defe206e4920c77eaf5f8a090772aefd`.
The pool contains 50 distinct empty-query filter/sort requests. After 20 warmups,
each version ran 50 calls at concurrency 1, then 50 at concurrency 5, repeated
three times. Connection initialization is excluded; each timing ends after the
complete parsed response. Incorrect/failed calls would contribute 10,000 ms.
The baseline GET violation was recorded separately so its latency could be measured.
No official performance points can be inferred: the hidden functional eligibility
threshold and runner network conditions were not evaluated.

Selected direct-search medians from the same container environment:

| Query / path | Starter | Improved dev run |
|---|---:|---:|
| Default exact page | 67.84 ms | 0.08 ms |
| Black dress | 317.78 ms | 27.89 ms |
| Prose-budget dress | 253.38 ms, empty | 14.72 ms, matching products |
| Mixed black jeans / white T-shirts | 264.40 ms, empty | 21.10 ms, both choices |
| Budget dress + accompanying bag | 269.03 ms, empty | 48.16 ms, dress and accessories |
| Comfortable lazy Sunday | 258.09 ms, empty | 203.87 ms, grounded options |

Raw evidence: [baseline dev](../evaluation/reports/baseline-dev.json),
[final dev](../evaluation/reports/final-dev.json),
[baseline held-out](../evaluation/reports/baseline-heldout.json),
[final held-out](../evaluation/reports/final-heldout.json),
[final all-case rerun](../evaluation/reports/final-all.json),
[baseline MCP](../evaluation/reports/mcp-baseline.json),
[improved MCP](../evaluation/reports/mcp-final.json).

The incremental development pass counts were 11 (starter), 11 (exact index),
18 (constraint parsing), 20 (field ranking/mixed choices), 21 (recommendations),
and 22 (generic-type preference refinement). Preordered exact pages then reduced
filter/sort latency while retaining 22 passes. Intermediate JSON reports retain
the actual results, including failures. Held-out queries were reserved during
tuning; no changes were driven by held-out failures. Final independent contract
review added inventory abstention and budget-scope regressions, followed by the
37-case rerun. Existing held-out cases are now consumed; use a fresh reserve for
future tuning decisions.

## Commands and environment checks

Run from the repository root (the local images are not published):

```powershell
py -3.14 -m venv .venv
# Sandbox setup initially needed a workspace TEMP and pip --python .venv.
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Get-FileHash data/products.json -Algorithm SHA256

docker build -t polaris-search:audit .   # done BEFORE implementation
docker run --rm polaris-search:audit python -m unittest discover -s tests -v
# Baseline evaluation used a bind mount of evaluation/ into the immutable image.

docker build -t polaris-search:local .
docker run --rm polaris-search:local python -m unittest discover -s tests -v
docker run -d --name polaris-final-check -p 127.0.0.1:8017:8000 polaris-search:local
docker exec polaris-final-check python smoke_test.py http://127.0.0.1:8000/mcp
.\.venv\Scripts\python.exe evaluation/mcp_check.py http://127.0.0.1:8017/mcp --output evaluation/reports/mcp-final.json
```

Local evaluation commands used `--split dev`, `--split heldout`, then `--split all`
with JSON output files under `evaluation/reports/`. Docker bind mounts saved reports
on the host. The baseline workload used `--allow-get-stream` solely to record its
GET violation without aborting the measurement. Container health, GET status,
product count, non-root user, dependency installation, smoke behavior and checksum
were checked. Temporary verification containers were removed after testing.

## Limits and remaining work

- The local set is small and deliberately interpretable. Its relevance rules give
  binary 0/3 grades from type/color/text predicates, and do not judge nuanced style,
  usefulness or all constraints as Bedrock would. A perfect local proxy score is
  not evidence of perfect semantic ranking. The unusual-area aggregate in the raw
  report includes zero proxy-grade placeholders for non-ranking cases; use the
  per-case data and empty-response checks rather than interpreting that aggregate
  as the official unusual score.
- Query interpretation is English-focused and rule-based. Reviewed typos and aliases
  are limited. Unknown words remain hard lexical requirements, so unusual but valid
  requests may be rejected. Broad occasions use a small catalog-grounded preference
  map, not comprehensive semantic understanding. Exact filters remain exact; natural
  unqualified colors include catalog shades in the same family.
- Ranking uses weighted token presence/IDF and phrase boosts, not BM25 term-frequency
  normalization. Balanced branches improve choice coverage but may sacrifice global
  relevance order. Distinct source variants are preserved, so similar variants can
  fill several slots. Clothing compatibility and audience inference are heuristics.
- Unsupported inventory/size/shipping/discount constraints abstain conservatively.
  No external attributes, brands, products or synthetic review claims are added.
- No semantic-model experiment demonstrated a gain here, so no vector service,
  checkpoint, training pipeline or paid inference was introduced. MODA's source,
  licenses, costs and incompatible assumptions are reviewed in the audit.
- Before further tuning, create a larger, independently judged development set and
  a fresh held-out set with graded relevance/complement labels. Measure broader
  paraphrases and abstention errors, then compare BM25 and optional offline semantic
  retrieval with the current implementation. Persist vector build metadata and
  original IDs if that experiment is justified. Profile large mixed queries,
  recommendations, deep offsets and multi-worker memory before any deployment.
- Deployment, paid infrastructure and official attempts still require explicit
  authorization. No official benchmark score is available.
