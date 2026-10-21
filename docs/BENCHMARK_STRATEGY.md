# Polaris benchmark strategy — 21 October 2026

**Attempt 1: NO-GO now.** The local release is reproducible and passes its current
checks, but no organizer-reachable deployment is verified and semantic readiness
is not established independently. Unreachable endpoints and protocol failures
consume attempts. Resolve deployment prerequisites and establish a fresh judged
local baseline before spending one of five runs. This document does not authorize
deployment or an attempt, and contains no official score or score prediction.

## Release and evidence

Baseline: `main`, commit `689e11b7e26d996e8615edaf0c854ebb8c244176`, tree
`5988fd2f881519f7e95dd1ae68eaadfcb56513d3`. Git status and index were clean before
this document. The old starter-HEAD blocker in [DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md)
has been resolved by that commit; its hosting and semantic uncertainties remain.
[RELEASE_CANDIDATE.md](RELEASE_CANDIDATE.md) describes the reviewed 36-file change.

The authority for the rules below is the supplied [hackathon brief](../hackathon-brief.md),
especially “Benchmark scoring,” “Ranking relevance and recommendations,” and
“Performance and competition rules.” These are verified repository rules, not a
claim that the separate benchmark website/runner has been independently inspected.
Also reviewed [AGENT.md](../AGENT.md), [AUDIT.md](AUDIT.md), [REPORT.md](REPORT.md),
the schemas, runtime modules, all seven test modules, evaluation cases and programs,
Dockerfile and requirements. No application, catalog, schema or historical result
file was changed for this strategy.

## Verified scoring weights and mechanics

| Area | Official cases | Maximum points | Exact category calculation |
|---|---:|---:|---|
| Validity and constraints | 30, including 10 invalid calls | 25 | `25 × mean(per-case validity score)` |
| Ranking relevance | 25 | 30 | `30 × mean(nDCG@10)` on single-intent relevance cases |
| Unusual or irrelevant | 10 meaningful unusual + 10 irrelevant/impossible | 15 | `7.5 × mean(unusual nDCG@10) + 7.5 × correct empty-response rate` |
| Mixed choices | 15 | 15 | `15 × mean(0.5 × choice coverage + 0.5 × nDCG@10)` |
| Complementary recommendations | 10 | 10 | `10 × mean(per-case recommendation score)` |
| Performance | Separate 300 timed calls | 5 | `5 × correct response rate × max(0, min(1, (2000 − p95_ms) / 1800))`, only when eligible |

The 100 functional cases sum to **95 points**. Performance requires both
**at least 85.5/95 functional points** and **at least 95% correct performance calls**;
otherwise it earns zero. Full latency credit is at 200 ms or below, zero at
2,000 ms or above. Low local latency alone establishes neither eligibility nor points.

An invalid validity case scores 1 for an accepted MCP error and 0 for success.
A valid case averages four binary checks: structure/IDs/references, constraints,
sorting/pagination, and expected presence/absence. Timeout, transport error or
malformed response zeros the entire case. Empty-query pages are checked exactly.

Bedrock grades semantic products 0–3. For rank `r` starting at 1,
`DCG@k = sum((2^grade_r − 1) / log2(r + 1))`. Normalize against **ten fixed grade-3
primary slots** or **five fixed grade-3 recommendation slots**, not the best grades
among returned products. Missing slots earn zero. Structurally invalid semantic
responses score zero; products violating hard constraints earn no gain.

Mixed coverage counts choices with at least one grade-2-or-3 choice match whose
primary grade is also at least 2 and which obeys hard constraints. One pooled list
shares the limit. Complement case quality averages primary nDCG@10 and complement
nDCG@5; each complement must satisfy its own constraints and reference an on-page
primary graded at least 2. A reviewed no-complement case gets full complement
credit for an empty recommendation list. Explanatory reasons are not scored.
Substitutes do not automatically qualify as complements.

Performance uses a frozen organizer pool of 50 empty-query filter/field-sort calls,
limit 10, offset 0; 20 warmups, then 50 calls at concurrency 1 followed by 50 at
concurrency 5, repeated three times. Pool all 300 timings; use nearest-rank p95.
Failed/incorrect/timed-out calls contribute 10,000 ms. Network time is included;
initial connection setup is excluded. Our pool follows this shape but is not the
organizer's pool.

Ordinary functional/performance calls have a 10-second deadline; validity probe
cases and connection/discovery have 30-second deadlines. The student execution
budget is 20 minutes excluding Bedrock waiting. Discovery failure scores zero;
student deadline expiry zeros unexecuted cases and performance. A separate one-hour
organizer cap voids the run and restores the attempt. Bedrock judgment failures
are organizer failures, with no guessed-score fallback. Temperature zero does not
guarantee identical judgments.

## Per-category local baseline

Fresh host check on this unchanged release: `evaluation/run.py --split all` passed
**37/37**, with case SHA-256
`3c706c84fbb27784680637f0ec1b402e055779e619ce44ac0d7553719cbdd46b`.
The table's detailed metrics come from the committed
[final-all.json](../evaluation/reports/final-all.json); fresh aggregate pass counts
and area means matched. All relevance numbers below are **student rule proxies**,
never Bedrock grades or official category scores.

| Official area | Current local evidence | Principal gap |
|---|---|---|
| Validity, 25 | 9/9 evaluation cases: 6 valid exact-page cases, 3 invalid calls; unit suite adds 240 exact fixture pages, types/ranges/nulls/ties/precedence/reference tests | Not the official 30 cases; direct Python exceptions are not transport evidence. Historical official smoke separately tests MCP errors |
| Ranking, 30 | 8/8; mean rule-proxy nDCG@10 **1.0000**, ten predicate-matching products each | Type/color/text predicates cannot distinguish direct, useful and weak style matches; no independently judged graded ranking baseline |
| Unusual/irrelevant, 15 | 3/3 meaningful queries, mean rule-proxy nDCG@10 **1.0000**; 6/6 negative queries correctly return both arrays empty | Only three positive paraphrase/typo examples; no robust estimate of false rejection or false acceptance |
| Mixed, 15 | 5/5; mean rule coverage **1.0000**, mean rule-proxy nDCG@10 **1.0000** | A choice predicate match is not a Bedrock grade ≥2; branch balance and variant diversity lack independent judgments |
| Complements, 10 | 4/4: two nonempty complement cases each have five matching recommendations and proxy nDCG@5 **1.0000**; one disabled-complement case and one impossible-accessory-budget case return no recommendations; primary proxy nDCG@10 **1.0000** throughout | Only two positive complement queries; compatibility and referenced-primary quality are not jointly semantically judged |
| Performance, 5 | 2/2 direct exact-page cases; committed real MCP workload **300/300 correct**, p50 **40.72 ms**, p95 **123.81 ms** | Two direct checks are not a performance score; real MCP samples are localhost and use our pool. Official functional eligibility and network latency unknown |

The unusual-area raw mean `0.3333` averages three graded positives with six
zero placeholders for empty-response checks. It is **not** an unusual relevance
score. Likewise zero nDCG placeholders for exact/invalid cases have no scoring
meaning. Do not weight the raw `areas` aggregates into a predicted total.

The historical dev/held-out counts were 22/22 and 15/15; both sets are now consumed.
The starter passed 19/37 across its baseline splits, versus 37/37 after improvements
([REPORT.md](REPORT.md)). That establishes local regression progress, not hidden
generalization. Keeping the existing `heldout` label does not restore independence.

Fresh host unit suite: **34/34**, 0.162 s reported test time. The first sandboxed run
stalled on the async routing test and was interrupted; the complete rerun outside
the Windows sandbox passed. Fresh direct evaluation startup was **4.915 s**, peak
process working-set measure **651.51 MiB**, native Python 3.14. This single sample
is not a startup distribution and is not directly comparable to Linux peak RSS.

Historical container evidence in [REPORT.md](REPORT.md) and
[DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md): unit tests and official supplied
smoke pass; local 1 GiB / 1 CPU readiness samples **8.26–9.54 s**; load/index
**5.41 s**, post-profile peak RSS **648.21 MiB**; post-workload container memory
**697.9 MiB**. A five-choice limit-100 search with recommendations took **1,505.47 ms**
in one direct sample. That is a latency risk to test, not an observed timeout.
The readiness MCP rerun p95 was **124.92 ms**, also 300/300 correct. Neither Docker
nor smoke nor MCP load testing was rerun during this documentation task; these
are dated prior measurements, not newly executed checks.

## What local success does not establish

- `run.py` uses 0/3 grades from catalog type, color, pattern, price and selected text
  predicates. It does not implement all four official validity subchecks for every
  semantic row, all natural-language constraints, graded choice judgments, or the
  recommendation anchor-grade gate. A boolean pass can occur with fewer than ten
  primary or five complement slots; fixed-ceiling quality still penalizes missing
  slots. Disabled recommendations are useful regression coverage, not a positive
  official complement-quality estimate.
- `query.py` recognizes a limited reviewed vocabulary. Unknown residual words are
  hard lexical requirements; meaningful paraphrases may be rejected. Conversely,
  removing common words or promoting occasion hints may admit weak matches.
  These are source-based risks, not measured hidden failures. Broader typo handling
  could increase false positives. Unsupported attributes must still cause abstention.
- `search.py` uses token-presence IDF, field weights and phrase boosts, not BM25
  term-frequency/length normalization. Mixed branches receive reciprocal branch-rank
  scores; this can favor balance over relevance. Catalog variants remain distinct.
  There is no official diversity bonus: variety helps only if coverage or relevance
  improves, and must not replace better matches merely to look diverse.
- `recommendations.py` uses a finite compatibility table, inferred audience and
  same/neutral-color preferences. A category-compatible bag is not necessarily a
  useful coordinated complement. The strongest primary anchor matters to official
  scoring. Better reasons alone cannot improve that score.
- The release has no measured semantic retrieval gain; MODA's published scores
  cannot transfer here. Models, services and complexity have no default entitlement
  to an attempt. Public images and synthetic reviews are not additional factual
  evidence. Product IDs, schema, exact catalog path and hard constraints remain fixed.
- Hosting port/probes, public Host/Origin values, worker settings, runner region/IP,
  ingress and evaluation window remain unconfirmed. Default Host restrictions reject
  an unlisted public hostname. `WEB_CONCURRENCY=2` reproduced startup failure; use one
  worker. No public endpoint exists. Long semantic concurrency, in-flight shutdown,
  memory growth and true cold-start behavior remain unmeasured.

## Three prioritized local experiments

These are proposed experiments, **not executed changes or promised gains**. First
create a fresh student-authored graded development set and sealed reserve, with
queries written independently of current aliases and before inspecting outputs.
Cover all six areas and audit catalog feasibility; include positive/negative
paraphrases, typos, impossible requirements, conflicting filters, per-item scopes,
mixed choices, complements, nulls, ties, pagination and no-complement situations.
Have reviewers judge anonymized pooled outputs on the supplied 0–3 rubric using
only catalog facts. Record IDs, primary/choice/complement grades and anchor validity;
resolve disagreements. These are local judgments, not recreated hidden tests.
Pre-register splits, metrics and acceptance rules before tuning; inspect the reserve
only once per selected candidate and retire it afterward.

| Priority | Experiment and unmeasured hypothesis | Benefit / cost / risk | Comparison and acceptance gate |
|---|---|---|---|
| 1 | Paraphrase/abstention calibration: inspect new baseline errors, then test one conservative parser/alias change at a time. Hypothesis: distinguish soft shopping language from factual requirements more accurately | Ranking 30 + unusual 15, potentially mixed/complements too; medium effort, medium constraint/false-positive risk | Measure positive-query false-empty rate, negative empty accuracy, hard-constraint violations and graded nDCG. Adopt only with positive paired semantic gain, no new negative-case failures or contract regressions; otherwise retain release |
| 2 | Fielded BM25 versus current ranking on the same admissible candidates, retaining phrase evidence. Hypothesis: field-length/term-frequency handling improves ordering beyond presence-based IDF | Ranking 30 and mixed quality 15; medium effort, medium ranking/startup/memory risk | Freeze parser/candidate sets for the ablation; compare per-query nDCG@10 and coverage on new dev/reserve, exact outputs on field sorts. Accept positive paired gain with uncertainty reported, no observed coverage/constraint regression, and target-resource latency/memory within confirmed limits. Do not infer candidate-recall gains from a reranker |
| 3 | Complement coordination and mixed coverage ablations, evaluated separately before combining. Hypothesis: stronger catalog-supported anchor/complement pairing and relevance-aware branch allocation improve graded utility | Complements 10 + mixed 15; medium effort, medium diversity/anchor/scope risk | Compare primary nDCG@10, complement nDCG@5 with anchor-grade gate, choice coverage and their official-shaped local means. Keep each change only if its target mean improves without observed loss in primary quality, hard constraints, empty-complement behavior or stable pagination. No global variant deduplication |

For all experiments, show per-query paired differences and confidence intervals
when sample size permits; a tiny or unstable gain is inconclusive. Freeze concrete
resource limits after confirming the target, rather than inventing a latency SLA.
Run regression tests for every behavioral change, host/container tests and official
public smoke, exact MCP workload, startup/memory and broad-query stress before
promoting a candidate. Do not overwrite historical reports. Record commit/tree,
catalog SHA, case/judgment checksums, environment, outputs, errors and timings.
Optional offline semantic retrieval is a later experiment only if fresh judgments
show remaining recall failures worth its cost; preserve original string IDs and
exact filtering/field sorting, with no per-request index rebuild.

## Five-attempt allocation and decision gates

Five is the team's total accepted-run budget across URLs. Queuing reserves a run;
only one queued/active run is allowed. Student-side reachability/timeouts/protocol
errors consume a run; confirmed organizer failures restore it. The best **complete
attempt** counts, without mixing category scores. Ties use functional score, then
lower p95, then earlier completion; missing performance uses 10,000 ms for the tie.

This is an adaptive allocation, not a requirement to exhaust the budget:

1. **Attempt 1 — establish an official baseline**, after the gates below and explicit
   authorization. Prefer the reviewed release unless a local experiment proves a
   better candidate. Do not spend a run simply to test endpoint reachability.
2. **Attempt 2 — address the largest evidenced deficit.** Use category scores,
   timings and generic failure counts plus independent local diagnoses. Official
   hidden queries/IDs are unavailable; do not reverse-engineer answers or invent them.
3. **Attempt 3 — promote the next independently validated change**, selected from
   experiments by actual deficits, not a fixed promise to add embeddings.
4. **Attempt 4 — validate a beneficial combination**, only after local ablations
   show gains survive integration. If nothing improves, preserve the attempt.
5. **Attempt 5 — retain as a final reserve** for the strongest measured candidate
   or a diagnosed student-side failure. A repeat without a change or clear rationale
   is low priority; do not use judge randomness as an optimization strategy.

For every authorized run, pin code, index, data and deployment configuration for
its duration; archive category/overall scores, generic failures, timings and runner
metadata actually supplied. Never change the live candidate during evaluation.
Every future deployment and attempt still requires the user's explicit authorization.

**GO gates for Attempt 1:** confirm the actual hosting contract and organizer ingress
details; obtain authorization for deployment; verify the immutable release, official
catalog digest, one worker, public allowlists, startup grace and resources on that
target; pass non-scored real MCP initialization/discovery, smoke, exact pages and
latency checks through the actual proxy; review fresh independently graded positives,
negatives, mixed and complement cases and document remaining risks; then obtain
explicit authorization to queue Attempt 1. None of these implies that a local
functional score predicts the hidden 85.5 threshold. If semantic evidence remains
inconclusive after endpoint readiness, an explicitly authorized exploratory baseline
may be reasonable, but its attempt cost and uncertainty must be accepted deliberately.

**Current checklist:** PASS — committed release identity and fresh local regressions.
BLOCKED — hosting contract and organizer reachability. UNMEASURED — official semantic
score and performance eligibility. **Highest-priority next action:** confirm the
hosting/organizer configuration without spending an official attempt; in parallel,
prepare the fresh independently judged local evaluation set. Attempt 1 remains NO-GO.

## Commands and verification scope

Executed for this document from the repository root in PowerShell:

```powershell
git branch --show-current
git rev-parse HEAD
git --no-optional-locks status --short --untracked-files=all
git diff --cached --stat
git diff --stat
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe evaluation/run.py --split all
```

The evaluation command had no `--output`, preserving all committed report files.
Document verification checks scoring table weights/counts against the brief, local
counts against cases and final report, relative links, unchanged HEAD/index/tracked
files and the absence of changes other than this new untracked document. No commit,
push, deployment, paid service, model download or official benchmark was performed.
