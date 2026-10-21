# Preserved parsing candidate — 21 October 2026

This report records existing uncommitted remediation based on
`2dd37a2a63377074f3f909a9bff1f2e489def570`. No additional search feature was added
during the public endpoint investigation. See [public deployment findings](PUBLIC_DEPLOYMENT_FIX.md)
for the current transport blocker and rerun results.

## Existing changes

`query.py` separates result counts, quantities, money, ratings and review counts;
recognizes negation, color alternatives and numeric-ID parity. `search.py` applies
those constraints before quantity selection/pagination and adds requested mixed
choice coverage/variety. `recommendations.py` propagates exclusions and parity.
`README.md` documents these capabilities and limitations. Public schemas, tool,
protocol, dependencies, server, Dockerfile and frozen catalog are unchanged.

New portable files: `tests/test_remediation.py`, `evaluation/advanced.py`,
`evaluation/advanced_cases.json`, `evaluation/reports/remediation-checks.json`,
`evaluation/reports/remediation-native-before.json`, and
`evaluation/reports/remediation-native-after.json`. Scratch profiling files are not
part of the candidate. The new cases use the seven exact user-authored requests,
not hidden organizer cases. The evaluator calls native MCP without reformulation
or client-side response filtering.

## Recorded before/after evidence

| Check | Before | After |
|---|---|---|
| Seven requests: supported constraint outcomes | 2/7 | 5/7 |
| Native checks including query-only and supplementary cases | 10/20 | 20/20 |
| Existing local proxies | 37/37 | 37/37 |
| Host/container unit suite after changes | — | 48/48 each |
| Supplied host/container smoke after changes | — | PASS each |

Requests 1 (parity/count/budget), 2 (sneaker constraints), 3 (mixed coverage),
4 (irrelevance) and 7 (impossible constraints) pass the local constraint checks
afterward. Requests 5 (already-owned outfit context) and 6 (multiple complete
outfits under a total budget) remain unsupported and return empty arrays. Four
of the 20 checks verify this safe abstention; they do not count as shopping
capability gains. Styling relevance remains heuristic and is not Bedrock judged.

`evaluation/reports/remediation-checks.json` preserves source hashes, catalog hash,
container identity and performance evidence. Single exact-page runs had p95
159.67 ms before and 203.93 ms after. Three later interleaved runs per version
had median run p95 138.62 ms before and 138.85 ms after; no consistent speed gain
or regression is established. Each run had 300/300 correct responses. Fresh-process
index-load medians were 4.78 s before and 4.93 s after, about 642 MiB peak memory;
these exclude imports/binding and use a warm filesystem, not a public cold-start SLA.

The recorded container image is
`sha256:f34ad3ab66103b7b80b7cc0fe3492be5ec2867262a6922bf8ad9a7f597eb659f`.
Its eleven inspected source files matched the candidate; Linux and Windows native
outputs matched across all 20 checks. Container health passed, UID was 10001 and
shutdown exited zero without OOM. These are prior measured checks, not a new build
performed during the Host diagnosis. The public incident report lists freshly
rerun host checks separately.

## Release limits

Candidate runtime files remain uncommitted; no new deployment SHA exists. The
reviewed release remains available as rollback. GO for reviewing/preparing an
immutable candidate after transport configuration is resolved; NO-GO for claiming
public readiness or spending another official attempt until public protocol checks
pass. Proxy correctness does not establish official ranking, recommendation,
semantic relevance or performance scores.
