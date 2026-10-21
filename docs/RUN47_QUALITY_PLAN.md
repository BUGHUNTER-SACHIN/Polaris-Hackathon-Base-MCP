# Run #47 quality review and proposed local changes

21 October 2026. Base HEAD and live fork/main:
`16e55eadc2b302514fb03c874efa4436c1977a96`.
Changes below are uncommitted and unstaged. No push, deployment, hosting setting
change, or official benchmark submission occurred during this work.

## Official evidence and opportunity size

The authenticated [Run #47 scorecard](https://admin-dashboard.01m5erq7wn81nf6mhfpqkjb0ka.apps.springwinter.dev/runs/47)
was inspected directly: complete, submitted 21 October 16:48 UTC, all 100 cases
evaluated, functional 67.10/95, 300 timed calls, correct rate 100.0%.
[Run #37](https://admin-dashboard.01m5erq7wn81nf6mhfpqkjb0ka.apps.springwinter.dev/runs/37)
was previously read directly and captured in `.audit-tmp/run37-scorecard.json`
and `.audit-tmp/RUN37_DIAGNOSIS.md`.

| Category | Maximum | Run #37 | Run #47 | Change | Remaining functional points |
|---|---:|---:|---:|---:|---:|
| Validity | 25 | 25.00 | 25.00 | 0.00 | 0.00 |
| Ranking | 30 | 0.00 | 20.66 | +20.66 | 9.34 |
| Unusual | 7.5 | 1.50 | 2.25 | +0.75 | 5.25 |
| Irrelevant | 7.5 | 7.50 | 7.50 | 0.00 | 0.00 |
| Mixed choices | 15 | 0.00 | 9.72 | +9.72 | 5.28 |
| Recommendations | 10 | 0.00 | 1.96 | +1.96 | 8.04 |
| Performance | 5 | 0.00 | 0.00 | 0.00 | Conditional |
| Overall | 100 | 34.00 | 67.10 | +33.10 | — |
| Official p95, ms | — | 1331 | 403 | -928 | — |

The formulas in `hackathon-brief.md` are the authority: ranking is 30 times
mean nDCG@10; unusual is 7.5 times mean nDCG@10; irrelevant is 7.5 times correct
empty-response rate; mixed is 15 times the mean of coverage and nDCG@10;
recommendations are 10 times the mean of primary quality at 10 and complement
quality at 5. Fixed reference slots mean missing products earn zero.

Performance requires at least **85.5/95 functional points** and 95% correct timed
calls. Run #47 fails the functional eligibility threshold. At exactly 403 ms
and 100% correctness, the conditional latency formula would award 4.4361 points.
Holding those quantities fixed, 91 overall would require about 86.5639 functional
points, an increase of 19.4639. This is conditional arithmetic, not a prediction.
The small changes here do not establish such a gain.

Hidden queries and grades are unavailable. These category totals cannot identify
which hidden prompts failed, or separate primary and complement quality inside
the recommendation score. No hidden cases were invented or accessed.

## Release and deployment truth

`git ls-remote --heads origin main` returned the expected full SHA. The working
tree was clean before this task. The running baseline container
`polaris-release-public-verify`, image `polaris-search:release-final`, remains
unchanged on port 8037. A separate candidate server runs on port 8047; the public
service was not replaced.

The public health endpoint returned HTTP 200 with
`{"status":"ok","products":105126}`. The supplied public smoke test passed.
All 39 existing quality responses and all 18 additional-case responses matched
the unchanged release baseline **exactly**, including IDs and recommendations.
That establishes sampled behavioral parity, not proof of deployed source identity.
No revision header was returned; the actual active SHA/image digest remains
unverified without SpringWinter's active deployment/build metadata.

## Prioritized, evidence-backed fixes in this proposal

| Priority / mechanism | Category / maximum | Reproduction and observed baseline | Smallest fix and regression | Estimated impact, uncertain |
|---|---|---|---|---|
| 1. Suffix complement grammar is left among hard search terms or mixed choices | Recommendations / 10; ranking / 30 | `a dress with a bag to match` returns no primary results; `shirt with a titanium belt to match` also loses the valid primary | Recognize an item-bearing suffix clause before ordinary parsing; keep primary attributes and accessory budgets/exclusions in scope. Unit tests cover disabled recommendations, unknown accessories, impossible budgets, and `dress with sleeves and a bag to match` | Restores known primary and accessory slots across clothing types. Official points unmeasured; cannot attribute all 8.04 missing recommendation points to this defect |
| 2. Explicit complement choices compete in one top-five pool | Recommendations / 10 | `black dress with a matching bag and sandals` returns five bags and no sandals; a fixture reproduces starvation despite eligible footwear | Reserve the best eligible product for each explicit complement choice, then fill and preserve score/ID ordering. Test uniqueness, current-page references and determinism | Measured accessory-choice coverage improves. Semantic usefulness of the selected complements is still ungraded |
| 3. `plus` is a literal term instead of a choice separator | Mixed / 15 | `a black dress plus a white bag under 2000` returns one white product named “Plus One Dress”; requested black-dress coverage is missing | Use the existing typed-choice parsing/constraint propagation for `plus`. Check scoped colors, budgets, stable pagination and unsupported branches | Improves this conjunction family across types; hidden-case frequency and score effect unknown |
| 4. Subjective synonym becomes a hard literal term | Unusual / 7.5; ranking / 30 | `something comfy for a lazy Sunday` returns one product because `comfy` is required literally | Treat `comfy` like the existing soft `comfortable` preference. Preserve explicit material terms, types, budgets and unsupported words | Restores ten slots in two catalog-backed examples. More slots do not prove better semantic grades |
| 5. Polite request prefix becomes a product requirement | Ranking / 30; other semantic categories | `I would love a red skirt under 2500` returns none | Remove only the leading `I/we would love` or contracted equivalent. Keep `love` elsewhere and unknown attributes as hard terms | Higher recall for this request form; official point gain unmeasured |

These repairs share the existing retrieval, exact-filter, sorting and pagination
paths. `search.py`, `server.py`, schemas, catalog, Dockerfile and dependency pins
are unchanged. Host/Origin protections and their regressions are unchanged.
No vector model, LLM, infrastructure dependency or speculative ranking rewrite
was introduced. Coverage reservations can trade a slightly higher existing
heuristic score for another explicitly requested accessory; that is intentional.
Only five recommendation slots exist, so more than five disjoint accessory
choices cannot all receive a product.

## Measurements and regression evidence

Seven fixture tests were added. Six failed against the original implementation
before the fix; the seventh specifically checks retention of primary attributes.
All seven pass afterward. The additional catalog cases were frozen before the
runtime changes: ten development cases and eight held-out type/rewording cases.
Held-out results were not used to tune the fix. These are student-authored
holdouts, not independent judge labels; they are now visible regression cases.

| Suite | Before | Candidate |
|---|---:|---:|
| Original Windows unit/security suite | 60/60 | 67/67, including seven new tests |
| Linux container unit/security suite | Earlier release baseline retained | 67/67 |
| Dependency check, host and container | PASS | PASS |
| Original proxies, development | 22/22 | 22/22 |
| Original proxies, held-out | 15/15 | 15/15 |
| Existing quality, development | 25/25 | 25/25 |
| Existing quality, held-out | 14/14 | 14/14 |
| Existing quality, native MCP | Public baseline 39/39 | Local 39/39 |
| Advanced native MCP | Prior release checks retained | 20/20 |
| Additional development, native MCP | 4/10 | 10/10 |
| Additional held-out, native MCP | 2/8 | 8/8 |
| Supplied smoke | Public PASS | Local PASS |
| Docker image build | Existing baseline preserved | PASS |

The advanced suite's owned-item and basket checks are safety/abstention passes;
they do not represent outfit planning capabilities. There were no observed
regressions on these suites. Passing tests cannot guarantee a future 25/25
official validity score.

Additional native case outcomes, with full IDs and responses archived in
`evaluation/reports/run47-expanded-before-native.json` and
`evaluation/reports/run47-expanded-after-native.json`:

| Case | Split | Before -> after | Primary count | Recommendation count |
|---|---|---|---|---|
| polite-skirt | dev | FAIL -> PASS | 0 -> 10 | 0 -> 0 |
| polite-unknown | dev | PASS -> PASS | 0 -> 0 | 0 -> 0 |
| plus-scoped | dev | FAIL -> PASS | 1 -> 10 | 0 -> 0 |
| plus-unknown | dev | PASS -> PASS | 0 -> 0 | 0 -> 0 |
| comfy-lounge | dev | FAIL -> PASS | 1 -> 10 | 0 -> 0 |
| comfy-unknown | dev | PASS -> PASS | 0 -> 0 | 0 -> 0 |
| suffix-accessory | dev | FAIL -> PASS | 0 -> 10 | 0 -> 5 |
| suffix-disabled | dev | FAIL -> PASS | 0 -> 10 | 0 -> 0 |
| suffix-budget | dev | PASS -> PASS | 10 -> 10 | 5 -> 5 |
| multiple-complements | dev | FAIL -> PASS | 10 -> 10 | 5 -> 5, both choices covered |
| polite-trousers | held-out | FAIL -> PASS | 0 -> 10 | 0 -> 0 |
| plus-accessories | held-out | FAIL -> PASS | 0 -> 10 | 0 -> 0 |
| comfy-cotton | held-out | FAIL -> PASS | 0 -> 10 | 0 -> 0 |
| suffix-coat | held-out | FAIL -> PASS | 0 -> 10 | 0 -> 5 |
| suffix-unsupported | held-out | FAIL -> PASS | 0 -> 10 | 0 -> 0 |
| suffix-negative | held-out | FAIL -> PASS | 0 -> 10 | 0 -> 5 |
| multiple-coat-complements | held-out | PASS -> PASS | 10 -> 10 | 5 -> 5 |
| plus-unsupported-material | held-out | PASS -> PASS | 0 -> 0 | 0 -> 0 |

Observed latency, nearest-rank percentiles of **different sequential samples**:

| Endpoint / sample | Calls | p50 ms | p95 ms |
|---|---:|---:|---:|
| Public, existing quality | 39 | 94.50 | 555.04 |
| Public, additional cases | 18 | 59.75 | 207.25 |
| Unchanged Linux baseline, additional cases | 18 | 27.76 | 469.47 |
| Windows candidate, additional cases | 18 | 39.24 | 279.33 |

For 18 calls nearest-rank p95 is the maximum. Different runtimes, caches, request
costs, and empty-response rates prevent a controlled latency-gain claim. These
are not the organizer's 300-call filter/sort performance workload. Official
403 ms remains the only Run #47 performance measurement.

Direct original-proxy process startup measured 11.50 s before and 4.12 s afterward;
peak process memory was 651.30 and 651.80 MiB respectively. Startup runs had
different cache/load conditions; no startup optimization was made or established.
The persistent search index is unchanged. Per-request complement coverage uses
temporary candidate-ID sets; worst-case peak request memory was not measured.

## Why a 91+ claim would still be unsupported; next experiments

1. **Primary semantic interpretation and contextual ranking** (30 ranking,
   7.5 unusual, and shared mixed/recommendation primary quality). Confirmed probe:
   `dress shoes for men` returns sneakers at the top because “dress” and “shoes”
   are extracted as separate types, with no compound-intent disambiguation.
   Also, `something comfortable for a lazy Sunday` returns baby hoodies first,
   yet the existing type-only proxy passes. Baby products are real catalog
   products; poor suitability for an unspecified shopper is a quality hypothesis,
   not proof of a hard-constraint violation. Next: freeze compound-type and
   explicit-audience/context fixtures, audit catalog footwear descriptions, and
   obtain independent relevance labels before changing type priorities or defaults.
   Smallest candidate: reviewed multiword type aliases plus evidence-based
   ranking among valid candidates. Keep explicit audience/category filters exact.

2. **Complement usefulness beyond category membership** (10 points). The current
   generic heuristic can return five near-identical bags. Existing tests accept
   their type/color/budget without judging outfit compatibility. Next: freeze
   diverse anchor/accessory pairs and negatives, inspect actual catalog facts,
   and independently grade usefulness. Trial a small coordination/diversity
   reranker only if judged quality improves without losing constraints or slots.
   Do not expand compatibility tables merely to fill five recommendations.

3. **Mixed and unusual generalization** (15 mixed, 7.5 unusual). The fixed repairs
   cover specific grammar families, not arbitrary natural language. Next: build a
   fresh reserved set of catalog-supported paraphrases, scoped constraints and
   negative requests beyond the four historical public probes. Compare branch
   coverage, grade distribution, missing slots and latency before adding aliases
   or relaxation rules. Unknown materials, brands and inventory must stay rejected.

Impact estimates for these experiments are uncertain and unmeasured. The category
headroom above is a ceiling, not expected gains. The local proxies have already
demonstrated an important measurement gap: high pass rates coexist with low
official recommendation/unusual scores. Independent semantic review is the
highest-value evaluation improvement before another official attempt.

## Exact commands and proposed release scope

All commands below were run; repeated invocations used separate before/after
output names. The baseline native server is the preserved committed release.
`--split all` executes both development and held-out partitions.

```powershell
git status --short
git log -1 --format='%H %s'
git ls-remote --heads origin main
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe evaluation/run.py --split all --output .audit-tmp/run47-original-after.json
.\.venv\Scripts\python.exe evaluation/quality.py --split all --output .audit-tmp/run47-quality-after.json
.\.venv\Scripts\python.exe evaluation/run47.py --split all --output .audit-tmp/run47-expanded-after-direct.json
.\.venv\Scripts\python.exe smoke_test.py https://web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev/mcp
.\.venv\Scripts\python.exe evaluation/quality_mcp.py https://web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev/mcp --output .audit-tmp/run47-public-quality.json
.\.venv\Scripts\python.exe evaluation/run47.py --url https://web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev/mcp --split all --output .audit-tmp/run47-expanded-public.json
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8047/mcp
.\.venv\Scripts\python.exe evaluation/quality_mcp.py http://127.0.0.1:8047/mcp --output .audit-tmp/run47-local-quality-native.json
.\.venv\Scripts\python.exe evaluation/advanced.py http://127.0.0.1:8047/mcp --output .audit-tmp/run47-advanced-after.json
.\.venv\Scripts\python.exe evaluation/run47.py --url http://127.0.0.1:8037/mcp --split all --output .audit-tmp/run47-expanded-before-native.json
.\.venv\Scripts\python.exe evaluation/run47.py --url http://127.0.0.1:8047/mcp --split all --output .audit-tmp/run47-expanded-after-native.json
docker build -t polaris-search:run47-review .
docker run --rm --network none polaris-search:run47-review python -m unittest discover -s tests -v
docker run --rm --network none polaris-search:run47-review python -m pip check
git diff --check
git diff -- query.py recommendations.py
```

Candidate startup used `Start-Process` with the workspace's
`.venv\Scripts\python.exe`, argument `server.py`, `PORT=8047`, hidden window,
and stdout/stderr redirected to `.audit-tmp/run47-server.*.log`.
The baseline container remains available on loopback port 8037. Restricted-shell
async tests stalled and were interrupted; the successful Windows unit and native
MCP runs used the unrestricted approved local shell. No application workaround
or security change was made for that environment issue.

Proposed files (nothing staged): `query.py`, `recommendations.py`,
`tests/test_run47.py`, `evaluation/run47.py`, `evaluation/run47_cases.json`,
`evaluation/reports/run47-expanded-before-native.json`,
`evaluation/reports/run47-expanded-after-native.json`, and this document.
Other detailed measurements remain in ignored `.audit-tmp/run47-*.json`.
The complete proposed patch, including new files, is in
`.audit-tmp/run47-proposed.patch`.

**Decision:** GO for reviewing this local diff as a bounded release candidate;
NO-GO for treating these proxy improvements as proof of 91+ or justification for
an official attempt. Obtain explicit publication authorization separately. The
single next action is review of this diff and the real catalog results before
any commit, push or deployment.
