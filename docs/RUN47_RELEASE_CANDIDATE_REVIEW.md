# Run #47 release-candidate review

22 October 2026 (IST). **Overall decision: REVISE; do not publish this candidate.**
The proposed trailing-matching parser can discard an explicit primary requirement.
The expanded unit suite and six native MCP adversarial cases fail. Historical
67/67 and 18/18 results in `RUN47_QUALITY_PLAN.md` remain valid records of the
earlier, narrower tests; they do not establish release readiness after this review.

## Preservation and scope

- HEAD remains `16e55eadc2b302514fb03c874efa4436c1977a96` on `main`.
- The original eight proposed files were reviewed and left byte-for-byte unchanged.
  No proposed application fix was implemented during this review.
- `.audit-tmp/run47-proposed.patch` is unchanged; SHA-256:
  `31f98f5f3ef7f2182db5f01461b2b29aed76c4c8f30059d0e501163c94257897`.
  Its reverse `git apply --check` succeeds against the original eight files.
- Original files and patch were copied without overwriting anything into
  `.audit-tmp/run47-rc-original/`; `manifest.json` records their byte hashes.
- This review adds `tests/test_run47_review.py` and this report. No files are staged.
- The public deployment, existing release container on port 8037 and original
  candidate server on port 8047 were not replaced. The latter was used for local
  MCP checks. A separate local image `polaris-search:run47-rc-review` was built for
  Linux tests; it was not pushed or deployed.
- No commit, push, reset, deployment, security-setting change or official attempt
  occurred. The public endpoint was not called during this review.

## Findings

### P1: a type word inside a garment attribute can erase the primary requirement

At `query.py:692-695`, presence of a recognized type in every raw clause is treated
as sufficient proof that the whole span is complementary. In:

```json
{"query":"dress with a shirt collar and a bag to match","include_recommendations":true}
```

`shirt collar` is treated as a Shirt item. The parser moves it into complements,
leaving an unrestricted Dress primary. The independent fixture has one dress with
the exact description “Cotton dress with sleeves and a shirt collar” and three
other dresses. Expected primary IDs: `["0001"]`; actual:
`["0001","0002","0003","0004"]`.

The same query through the full-catalog MCP candidate returns ten primary IDs:
`0192460006`, `0202017055`, `0212629004`, `0212629031`, `0212629032`,
`0212629033`, `0212629035`, `0212629036`, `0212629040`, `0212629043`.
The response includes products without even generic collar evidence in their name
or description. The catalog contains 1,467 dresses with collar evidence; the
failure is not explained by a complete absence of collared dresses. This count
does not assert that all 1,467 satisfy the more specific shirt-collar requirement.

The committed implementation is also imperfect: the same fixture query returns
`0001` and Shirt `0030`, conflating garment attributes with product types. The
proposal additionally loses the collar constraint and returns plain dresses.
This is a confirmed adverse change, not proof that HEAD handles the query correctly.

**Required revision:** preserve the primary attribute span. Type-token recognition
alone cannot establish item boundaries. Resolve compound garment attributes before
moving text into complements, and retain the strict `0001` fixture oracle. Do not
fix the failure by dropping `collar` or admitting plain dresses into the test.

### P1: suffix detection splits unit-bearing clauses before the existing protections

The suffix guard uses raw `re.split(and|or)` before `choices()` can protect price
ranges and color alternatives. Both of these valid queries return empty arrays:

```text
dress with a bag between 300 and 700 to match
dress with a black or white bag to match
```

The first splits the range's `and`, creating an untyped numeric clause. The second
splits the color `or`, creating an untyped color clause. `all(i.types...)` rejects
the split, and residual `match` contaminates ordinary retrieval. Both failures
reproduce through native MCP. Fixtures contain valid primary dresses and eligible
bags, with exact expected bag IDs and inclusive price/color checks.

**Required revision:** reuse unit-aware clause protection for both the guard and
actual choice parsing. Do not introduce another independent money/color parser.
Both were already zero-result gaps in HEAD; they are unresolved coverage defects,
not newly introduced false positives.

### P1: negative or unsupported accessory clauses erase valid primary results

The type-only gate also rejects:

```text
dress with a bag and no sandals to match
dress with a bag in stock to match
dress with a laptop to match
```

An exclusion-only clause has no positive type. An unsupported stock requirement
returns an unsupported intent before type extraction. An out-of-catalog product
type has no recognized type. Consequently, the suffix is not separated and the
whole primary search becomes empty.

The stock and laptop queries were tested with recommendations both disabled and
enabled in fixtures, and disabled through native MCP. The brief explicitly says
to ignore the complementary portion when recommendations are disabled. These
calls should still return the available primary dresses. With recommendations
enabled, unsupported accessories must remain empty; a laptop-compartment bag
must not be substituted for a laptop. The negative-accessory query should retain
eligible bags and exclude sandals.

**Required revision:** distinguish accessory scope from accessory satisfiability.
Unsupported accessory requirements must not bypass scope handling. Preserve
negative intents without turning them into positive choices. HEAD has the same
zero-result gaps; the proposed feature does not resolve them.

### P2: the new evaluator does not retain every case failure in its report

In `evaluation/run47.py:40`, the MCP/tool call occurs outside the per-case `try`.
Only `AssertionError` is handled within the evaluation block. A tool error,
transport failure or schema `ValidationError` can abort the run before the report
is written. This fails closed with a nonzero process exit; it is not a false-pass
or an application defect. It limits diagnostic completeness.

**Recommended revision:** record expected tool/transport/schema failures as failed
case rows, retaining their safe error details, then return a failing exit code.
Do not convert errors into valid empty search responses. This finding follows
from code inspection; no server outage or malformed-response experiment was run.

## Decisions for every material change

| Material change | Decision | Evidence and limits |
|---|---|---|
| `plus` as a typed-choice separator | ACCEPT | Independent fixtures verify scoped colors/budgets, explicit-filter precedence, category exclusions, partial availability, ascending-ID field ties and stable pagination. Unsupported branches are not filled with invented products. This does not imply arbitrary material phrases containing “plus” are understood. |
| Leading polite request prefix | ACCEPT | Quantity/material/budget survives `I’d love...`; a real fixture product named “Love slogan dress” is still found with and without the polite prefix. Prefix-only punctuation and unknown materials remain empty. |
| `comfy` as an existing soft comfort preference | ACCEPT, bounded | Explicit cotton, price and excluded-color requirements remain hard; unrelated laptops and unknown materials remain empty. No other synonyms were added. Comfort/breathability is not established as a catalog fact or independently graded. |
| Trailing matching instructions | REVISE, release blocker | Six strict test methods fail; primary-attribute loss is an adverse change. Range/color/negative/unsupported accessory scope is incomplete. Do not publish the current guard. |
| Explicit recommendation category coverage | ACCEPT, bounded | Eligible categories receive coverage while budgets, color/category exclusions, uniqueness and current-page references are preserved. Impossible/substitute choices remain empty. Generic/single-choice selection retains its score order. Semantic outfit usefulness is still unmeasured; category membership does not establish judge relevance. |
| Original seven fixture tests | RETAIN and EXTEND | They test real behavior, but the parser-term assertion in the comfy test is implementation-oriented and not a quality oracle. They missed the six scope failures. Twenty-one independent adversarial methods now test observable IDs/facts and contract behavior. No original expectations were changed. |
| New evaluator | REVISE diagnostics | Its normal-path grounding, constraints and coverage checks are useful. Preserve nonzero failure status while retaining per-case error evidence. |
| Frozen 18 cases and two response reports | ACCEPT as historical proxies | Manifest hashes match both reports. Ten dev and eight reserved cases are authored regression data, not independent semantic judgments or hidden cases. No expectations or artifacts were edited to get a pass. |
| Quality plan | RETAIN as historical; qualify with this review | Its score arithmetic and uncertainty warnings stand. Earlier green suites do not override current failing adversarial tests. This review supersedes any inference that the candidate is ready to publish. |

## Test validity and results

The new review fixtures explicitly supply product type, category, source text,
price, color and rating/null facts. Expected IDs are specified independently of
parser internals or production retrieval helpers. Catalog records are not altered.
The mixed-choice partial-availability test expects only actual eligible products;
it does not weaken a prior expectation or invent a product for an impossible branch.

| Check | Actual result |
|---|---|
| Windows full unit/security suite | **FAIL:** 88 methods; 6 failing methods, 8 failure records, zero errors; exit 1 |
| Linux full unit/security suite | **FAIL:** same six methods/eight failure records; exit 1 |
| Original 67 unit/security methods | PASS on both platforms |
| New independent adversarial methods | 15/21 pass; six fail |
| Original proxies, dev / held-out | 22/22 and 15/15; 37/37 overall |
| Existing quality, dev / held-out | 25/25 and 14/14; 39/39 overall |
| Existing quality through local MCP | 39/39 |
| Frozen additional cases, direct and native MCP | 18/18 each; dev 10/10 and reserved 8/8 |
| Advanced native MCP checks | 20/20; owned-item/basket safety checks remain capability limitations |
| New full-catalog native scope probes | **FAIL: 0/6**, valid MCP responses but wrong search behavior |
| Supplied local smoke | PASS, initialization/exact schemas/structured payload/search/validation |
| Host and Linux dependency checks | PASS |
| Separate local Docker build | PASS; container unit execution fails as above |
| Original patch/file preservation | PASS, byte hashes and reverse-check |
| Server, schemas, dependencies, Dockerfile, `search.py` | Match committed HEAD after line-ending normalization |
| Official catalog | SHA-256 remains `05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073` |

All failing unit assertions are in the added review file. The two stock/laptop
methods each have two failing subtests, explaining eight failure records across
six methods. Assertions were neither skipped nor marked expected failures.

Successful protocol, explicit-filter, field-sort, tie/null, pagination and security
checks are important evidence but cannot guarantee a future official 25/25. The
collar example violates an unambiguous nonempty-query requirement even though
schemas and catalog grounding are valid. The previous official score is not a
release-wide guarantee that can be carried forward to untested changes.

Native latency samples: existing quality p50 27.40 ms / p95 151.84 ms (39 calls);
additional cases p50 32.64 / p95 229.11 ms (18 calls); failing scope probes p50
19.30 / p95 122.46 ms (six calls). These sequential local samples are not the
official workload. Fast incorrect responses do not establish performance readiness.

## Reproduction, artifacts and exact diff

From the repository root, using the existing local candidate on port 8047:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_run47_review.py -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe evaluation/run.py --split all --output .audit-tmp/run47-rc-original.json
.\.venv\Scripts\python.exe evaluation/quality.py --split all --output .audit-tmp/run47-rc-quality.json
.\.venv\Scripts\python.exe evaluation/run47.py --split all --output .audit-tmp/run47-rc-expanded-direct.json
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8047/mcp
.\.venv\Scripts\python.exe evaluation/quality_mcp.py http://127.0.0.1:8047/mcp --output .audit-tmp/run47-rc-quality-native.json
.\.venv\Scripts\python.exe evaluation/advanced.py http://127.0.0.1:8047/mcp --output .audit-tmp/run47-rc-advanced.json
.\.venv\Scripts\python.exe evaluation/run47.py --url http://127.0.0.1:8047/mcp --split all --output .audit-tmp/run47-rc-expanded-native.json
docker build -t polaris-search:run47-rc-review .
docker run --rm --network none polaris-search:run47-rc-review python -m unittest discover -s tests -v
docker run --rm --network none polaris-search:run47-rc-review python -m pip check
git apply --reverse --check .audit-tmp/run47-proposed.patch
git diff --check
git status --short
```

Both unittest commands intentionally exit 1 until the defects are fixed. The
fixture IDs and full assertions are in `tests/test_run47_review.py`. Inline Python
MCP probes captured complete structured/text responses, catalog facts and latency
in `.audit-tmp/run47-rc-native-adversarial.json`. The committed-source fixture
counterfactual is in `.audit-tmp/run47-rc-head-counterfactual.json`.
Other evidence: `.audit-tmp/run47-rc-summary.json`,
`run47-rc-final-unit.log`, `run47-rc-final-linux-unit.log`, and the per-suite
`run47-rc-*.json` files. Full logs include the failing assertions, not just counts.

The original eight-file patch remains `.audit-tmp/run47-proposed.patch`.
The review adds only this document and `tests/test_run47_review.py`.
`.audit-tmp/run47-rc-review-additions.patch` contains exactly those two additions;
`.audit-tmp/run47-rc-reviewed.patch` contains the complete ten-file proposal against
HEAD, including all new files. None of these files has been staged.

**Next action:** revise the trailing-matching parser against the retained failing
tests before preparing another release snapshot. Accept the bounded plus/prefix/
comfy/coverage changes individually; reject publication of the current combined
candidate. Do not relax test expectations to preserve the earlier green totals.
