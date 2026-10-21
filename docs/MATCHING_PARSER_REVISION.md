# Run #47 matching-parser revision

22 October 2026 (IST). **Recommendation: ACCEPT the revised local candidate for
review. Publication remains unapproved.** No commit, push, public deployment,
SpringWinter setting change or official benchmark attempt occurred.

HEAD remains `16e55eadc2b302514fb03c874efa4436c1977a96`. There is no new release
commit. The public service and the original release container on port 8037 were
not modified. The old proposed candidate on port 8047 remains available.

## Preservation

Before editing, all ten existing changed/untracked project files and three patch
artifacts were copied into `.audit-tmp/run47-parser-revision-input/`, with a byte
SHA-256 manifest. The earlier original eight-file proposal also remains in
`.audit-tmp/run47-rc-original/`. Archive hashes were checked again after testing.
Live source files were revised only after these snapshots; original versions are
recoverable byte-for-byte. No original tests, cases, expectations, historical
reports or reviewed patch files were overwritten.

Preserved patch hashes:

- Original proposal: `31f98f5f3ef7f2182db5f01461b2b29aed76c4c8f30059d0e501163c94257897`.
- Reviewed proposal: `541ee3251b83d404d19aad40cc2a50528e1bbb2c28687a6bb1c6218151f399f8`.

## Root causes and structural fixes

| Failure | Root cause | Revision and evidence |
|---|---|---|
| Shirt-collar requirement disappeared | A type token inside an attribute was treated as an accessory item boundary | A grammatical attribute-head vocabulary identifies type-modified attributes before product-type extraction. `shirt collar` stays in the primary intent as lexical terms and a required normalized source phrase. Retrieval checks the phrase against the original name/description. The retained fixture returns only `0001`; Shirt `0030` and plain dresses are excluded. |
| Accessory price range produced no results | Raw `and` splitting treated the range as separate choices | Both ordinary choices and suffix scope detection use shared connector spans protected by money ranges, color alternatives, negative color chains and rating units. Primary and accessory ranges remain separate dictionaries. |
| Color alternatives produced no results | Raw `or` splitting created an untyped clause | Protect the full color-alternative span, then parse the alternatives within one intent. `black or white` is a union, not an AND requirement or separate product choice. |
| `bag and no sandals` erased the primary | Exclusion-only clauses failed the positive-type gate | Complement scope is located before availability checks. Pure negative accessory clauses attach exclusions to positive accessory intents; they never become affirmative sandal requests. |
| Unsupported stock requirement erased the primary | Unsupported intent returned before its type/scope could be retained | Parse scope/type/filters and retain an unsupported flag. No stock facts are invented; recommendations for that unsupported accessory remain empty, while primary dresses remain available. |
| Laptop accessory erased the primary or risked a laptop-bag substitution | Type recognition was incorrectly used to decide whether a complement existed | A nominal accessory clause may have an unsupported head. Explicit untyped accessory nouns remain unsupported; a laptop word inside a bag description cannot satisfy a laptop request. Primary results survive when recommendations are disabled or enabled. |
| Separate primary/accessory ranges initially failed a new test | The money regex consumed trailing whitespace, and connector detection checked that whitespace instead of the connector token | Span protection now tests the actual connector position. The independent two-range fixture and mixed-range catalog case both pass. |
| Common primary garment parts initially failed new tests | Indefinite phrases such as `a hood` were being treated as unknown accessory items | General garment-part/attribute head classes preserve hood, zip, slit, embroidery and design clauses on the primary. A cross-part fixture verifies intent terms, exact IDs and accessory references. No whole-query special cases were added. |

Existing plus choices, polite request prefixes, bounded comfy preferences and
recommendation category coverage are retained. `recommendations.py` additionally
copies phrase constraints into scoped intents and their cache keys. The six-line
addition to `search.py` checks source phrase evidence; explicit filter matching,
exact empty-query enumeration, sorting, ties, null ratings and pagination are
unchanged. Runtime responses still contain only the published fields.

## Intent, constraints and product evidence

The exact six native requests that failed the review now pass **6/6**, compared
with 0/6 before. Complete arguments, parsed-intent projections, IDs and references
are in `.audit-tmp/matching-verified-retained-six.json`.

Eleven additional catalog cases check declared semantic plans as well as returned
IDs, numeric lower/upper bounds, colors, exclusions, uniqueness and current-page
recommendation references. All pass directly and over both Windows and Linux MCP.
Native Windows/Linux payloads are identical for these eleven cases.

| Example | Actual outcome |
|---|---|
| `dress with a shirt collar and a bag to match` | Primary `0743126001`; bag recommendations `0241436001`, `0386681012`, `0428454001`, `0436570008`, `0436570024`, each referencing that primary |
| `dress between 900 and 1400 with a bag between 300 and 700 to match` | Ten dresses satisfy 900–1400; five bag recommendations satisfy 300–700; parsed budgets remain in their separate categories |
| `dress with a black or white bag to match` | Ten dresses and five bags; every bag is Black or White |
| `dress with a bag and no sandals to match` | Ten dresses and five eligible bags; the accessory intent excludes Sandals |
| `dress with a bag in stock to match` | Ten primary dresses, no recommendations; no invented inventory |
| `dress with a laptop to match` | Ten primary dresses, no recommendations, with recommendations either disabled or enabled |
| `dress with an unobtainium blend and a bag to match` | Both arrays empty; the unknown primary material is retained as a mandatory term |

The catalog has exactly one Dress with the literal source phrase `shirt collar`.
That independent catalog count was established before the new case expectation;
the new case has a one-product reference pool. None of the existing 37/39/18/20
case expectations was reduced. Fewer source-supported results are preferable to
filling ten slots with unsupported attributes.

`evaluation/reports/matching-revision-scope.json` contains all eleven complete
responses, expected semantic rules, parsed intents, IDs, references and resolved
catalog facts. IDs retain their original string values, including leading zeros.
The frozen catalog hash remains
`05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073`.

## Evaluation diagnostics

`evaluation/run47.py` now records query/arguments, expected intent, parsed intent,
primary/recommendation IDs, error type and failing stage. Schema, tool, constraint,
timeout and unexpected case errors become failed report rows, never successful
empty tool responses. Connection/discovery/session errors also produce a failing
exit, including teardown errors after completed calls. Unexecuted tool calls have
null latency; an unavailable endpoint does not appear artificially fast.

Tests inject timeout, malformed-schema and unknown-ID responses and check the
diagnostics. An intentional connection refusal at loopback port 1 returned exit 1
and retained diagnostics for all ten unexecuted development cases, with null p95.
That deliberate negative test is successful verification of failure reporting,
not a passing product-search run.

Direct evaluations show the actual local catalog parser plan. MCP does not expose
internal intent, so native reports explicitly label the plan as a local-source
projection. Seven runtime/schema/dependency file hashes in the running Linux test
container match local files; no claim is made that public-server internals were
inspected. No diagnostic fields were added to the MCP response schema.

## Final verification

| Check | Result |
|---|---|
| Windows full unit/security suite | **98/98 PASS** |
| Linux full unit/security suite | **98/98 PASS** |
| All 21 retained adversarial review methods | PASS, original assertions unchanged |
| New semantic-intent/diagnostic methods | 10/10 PASS, including garment-part subtests |
| Original 37 proxies | 37/37; development 22/22, held-out 15/15 |
| Existing quality cases | 39/39; development 25/25, held-out 14/14 |
| Existing quality over revised Windows MCP | 39/39 |
| Frozen Run #47 cases, direct/native | 18/18; development 10/10, held-out 8/8 |
| Advanced native MCP checks | 20/20 |
| New scope/intent cases | 11/11 direct; 11/11 Windows MCP; 11/11 Linux MCP |
| Exact six retained failing native requests | 6/6 PASS |
| Supplied Windows and Linux local smoke tests | PASS |
| Host and Linux dependency checks | PASS |
| Final local Docker build | PASS |
| Intentional evaluator failure tests | PASS; unavailable endpoint exits 1, no fabricated timing |
| Catalog, schema, dependency and security preservation | PASS |

Additional native scope p95 was 149.05 ms on Windows and 130.69 ms on the local
Linux test container, each an eleven-case sequential sample. These are local
workloads, not official benchmark measurements or a controlled latency-gain claim.
The original-proxy process measured about 651.64 MiB peak memory and 3.74 seconds
startup in this environment; no index-memory or cold-start improvement is claimed.

One initial Linux command had a shell guard typo after successful tests. It was
corrected and rerun with successful exit status. The newly discovered range and
garment-part assertion failures were fixed in code; no assertions were weakened,
skipped or marked expected failures.

## Exact changed files and commands

Changes relative to the preserved review input:

- Revised: `query.py`, `search.py`, `recommendations.py`, `evaluation/run47.py`.
- Added: `tests/test_matching_parser_revision.py`,
  `evaluation/matching_revision_cases.json`,
  `evaluation/reports/matching-revision-scope.json`, and this report.

The original tests, cases and historical reports are unchanged. `server.py`,
Dockerfile, dependency pins and both published schemas match HEAD. Host/Origin
protection, `search_products`, and MCP revision `2025-11-25` are unchanged.

Commands run from the repository root (output names distinguish intermediate
and final verification):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe evaluation/run.py --split all --output .audit-tmp/matching-final-original.json
.\.venv\Scripts\python.exe evaluation/quality.py --split all --output .audit-tmp/matching-final-quality.json
.\.venv\Scripts\python.exe evaluation/run47.py --split all --output .audit-tmp/matching-final-frozen-direct.json
.\.venv\Scripts\python.exe evaluation/run47.py --cases evaluation/matching_revision_cases.json --split all --output .audit-tmp/matching-final-scope-direct.json
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8051/mcp
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8052/mcp
.\.venv\Scripts\python.exe evaluation/quality_mcp.py http://127.0.0.1:8051/mcp --output .audit-tmp/matching-final-quality-native.json
.\.venv\Scripts\python.exe evaluation/advanced.py http://127.0.0.1:8051/mcp --output .audit-tmp/matching-final-advanced.json
.\.venv\Scripts\python.exe evaluation/run47.py --url http://127.0.0.1:8051/mcp --split all --output .audit-tmp/matching-verified-frozen-native.json
.\.venv\Scripts\python.exe evaluation/run47.py --url http://127.0.0.1:8051/mcp --cases evaluation/matching_revision_cases.json --split all --output .audit-tmp/matching-release-scope-native.json
.\.venv\Scripts\python.exe evaluation/run47.py --url http://127.0.0.1:8052/mcp --cases evaluation/matching_revision_cases.json --split all --output .audit-tmp/matching-release-scope-linux-native.json
.\.venv\Scripts\python.exe evaluation/run47.py --url http://127.0.0.1:1/mcp --split dev --output .audit-tmp/matching-verified-connection-failure.json
docker build -t polaris-search:matching-revision-verified .
docker run --rm --network none polaris-search:matching-revision-verified python -m unittest discover -s tests
docker run --rm --network none polaris-search:matching-revision-verified python -m pip check
git diff --check
git status --short
git rev-parse HEAD
```

The connection-refusal command intentionally exits 1; all successful suite commands
exit 0. Windows startup uses the repository venv's `python.exe server.py`, with
process-local `HOST=127.0.0.1`, `PORT=8051`, hidden window and separate preserved
logs. Linux native verification uses the local container
`polaris-matching-revision-final`, loopback port 8052, one CPU and 1 GiB memory.
The final verified image also includes the completed evaluator session diagnostics;
the running test container has identical application/runtime source.

`.audit-tmp/matching-parser-revision.patch` is the delta from the archived review
input. `.audit-tmp/matching-parser-candidate.patch` is the complete proposal against
HEAD, including the retained historical files and all new files. Nothing is staged.

## Remaining limitations and decision

- The parser is a bounded deterministic grammar. Its garment-part vocabulary is
  finite, and ambiguous or bare unknown accessory heads may be rejected. It is not
  a general language-understanding system; new phrasing still needs adversarial
  coverage and source-evidence review.
- Untyped named accessories fail closed. This prevents laptop-bag substitutions
  but can reject valid generic material-only accessory wording until its intent is
  unambiguous. Known typed requests such as cotton bags retain the cotton term.
- Compound attributes require a normalized literal source phrase. This is
  deliberately conservative and can miss semantically equivalent descriptions.
- Category coverage does not establish styling quality. The held-out/proxy cases
  are not independent semantic judge labels. Basket and owned-item outfit planning
  remain outside the native capability measured here.
- These local results establish regression behavior, not a future 25/25 validity
  guarantee, a public rollout, or a predicted official score. No 91+ claim is made.

**ACCEPT these revisions as a tested local candidate.** Any publication requires a
separate, explicit authorization and an exact reviewed snapshot. The production
release has not been changed.
