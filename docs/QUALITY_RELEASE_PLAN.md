# Quality candidate and release truth — 21 October 2026

**Publication addendum:** the user subsequently confirmed the fork's `main` in
SpringWinter settings and authorized the reviewed commit/push/redeploy workflow.
See [release verification](RELEASE_VERIFICATION.md) for the corrected one-product
test reference, preserved original 38/39 evidence and current release gates.
The measurements and unknowns below describe the earlier pre-publication state.

**Decision: GO for review of this local release candidate; NO-GO for another
official attempt.** The reviewed implementation is not behaviorally present on
the public endpoint, and no evidence yet supports a 91+ forecast. No commit,
staging, push, public setting change, deployment or official attempt was made.
This report supersedes the current-state statements in earlier incident reports;
their observations and measurements remain historical evidence.

## 1. Release identity: verified facts versus unknowns

| Item | Verified identity |
|---|---|
| Working branch / HEAD | `main`, `2dd37a2a63377074f3f909a9bff1f2e489def570` |
| Reviewed runtime release | `689e11b7e26d996e8615edaf0c854ebb8c244176`; next commit `2dd37a2` adds strategy documentation |
| Live `origin/main` | `e1cbc5fe8d4831719c530309075cccea2a278401`, starter; local main is ahead by two commits |
| Fork remote | `https://github.com/BUGHUNTER-SACHIN/Polaris-Hackathon-Base-MCP.git` |
| Upstream remote | `https://github.com/SpringWinter-Research/Polaris-Hackathon-Base-MCP.git` |
| Intended new Git release | Current candidate based on `2dd37a2`; **uncommitted, no new SHA exists** |
| Tested local candidate image | `polaris-search:quality-candidate`, ID `sha256:6677fef3298ad2f1c57b0962be65245f3a6047896054c18a875c0eb2be737197` |
| Prior candidate image preserved | `polaris-search:remediation`, ID `sha256:f34ad3ab66103b7b80b7cc0fe3492be5ec2867262a6922bf8ad9a7f597eb659f` |

The user confirmed that SpringWinter is connected to GitHub. The actual connected
repository, selected branch, built commit/image, auto-deploy trigger and logs are
**not established**. The supplied Run #14 page is the benchmark dashboard; its
visible navigation does not provide deployment settings or server logs. There is
no deployment manifest in the repository. Public health and MCP metadata provide
only product count and `polaris-product-search` version `1.0.0`, not a Git SHA.

Read-only public GitHub API checks returned HTTP 200 for the fork's deployments
endpoint with `[]`, and for `/commits/main/status` with SHA `e1cbc5f`, no statuses,
and aggregate state `pending`. Empty records are absence of deployment evidence,
not proof of any particular deployed SHA. Do not equate the tested local image
digest with the running public artifact or assume it is published to a registry.

**Verified mismatch:** four exact existing student-authored queries were rerun
through actual MCP on the public endpoint, the preserved release on port 8000,
and the fresh candidate on port 8035. The original starter was evaluated locally
from its Git source as an additional comparison. No organizer hidden cases were
obtained or invented.

| Exact query / arguments | Public results / recs | Release results / recs | Fresh candidate results / recs |
|---|---:|---:|---:|
| `I am looking for a black dress under INR 2000` | 0 / 0 | 10 / 0 | 10 / 0 |
| `dress and bag` | 0 / 0 | 10 / 0 | 10 / 0 |
| `a dress under INR 2000 with a matching bag under INR 1000`, `include_recommendations=true` | 0 / 0 | 10 / 5 | 10 / 5 |
| `black sneekers` | 0 / 0 | 10 / 0 | 10 / 0 |

All four public payloads equal the starter payloads. This strongly supports stale
search code but does not prove source identity. If the service builds this fork's
`main`, that remote currently cannot include either reviewed local commit. Other
possibilities include a different repository/ref, retained image or stale build.

Public health was HTTP 200 with `{"status":"ok","products":105126}`; initialize
was HTTP 200 with protocol `2025-11-25`; the supplied public smoke passed during
the investigation. Passing that smoke does not distinguish starter search from
the reviewed engine. The previous 421 incident is not the current blocker.

## 2. Preserved work and smallest additional changes

All previous dirty files were preserved. Pre-quality copies of runtime sources,
README, advanced evaluator/cases and remediation tests are in ignored
`.audit-tmp/quality-baseline-20261021/`. `search.py` and `recommendations.py`
were not changed in this quality sprint; their earlier fixes remain intact.

The additional runtime edit is **only `query.py`**:

- Recognize request/choice grammar (`recommend`, `suggest`, `both`, `either`)
  without requiring those words in catalog text. Unknown material/brand terms
  remain requirements; an unspecified request does not enumerate the catalog.
- Parse `within`, `budget of`, `no more than` and `no less than` as price bounds.
  Consume result-count units before monetary parsing.
- Consume explicit star-unit lower bounds before money and quantity extraction.
  This fixes `rated 4 stars and above` and `4+ stars` without adding public fields.
- Canonicalize reviewed `off-white`, `navy-blue` and `polka-dot` aliases. This fixes
  a real color leak: white off-shoulder descriptions could satisfy residual `off`
  while the query intended the exact Off White color.

No retrieval/ranking architecture, recommendation algorithm, dependency, catalog,
schema, server, Dockerfile, security setting or index format was changed in this
sprint. There is no vector model/service. Earlier uncommitted ranking/parser/
recommendation changes remain part of the intended candidate, not committed HEAD.

`tests/test_quality.py` adds eight regression methods with negative cases and
explicit-filter precedence. They were run before implementation and demonstrated
failures. `tests/test_transport_security.py` adds three methods checking a fresh
process's environment parsing and allowed/rejected Hosts, port forms, loopbacks,
lookalike domains, Origins and Content-Type. DNS-rebinding protection stays enabled.

## 3. Measurements and evaluation limits

| Check | Result actually measured |
|---|---|
| Candidate Windows unit/security suite | 59/59, 1.473 s in final formatted run |
| Candidate Linux/Python 3.12 unit/security suite | 59/59, 1.015 s |
| Committed release export unit suite | 34/34, 0.119 s during release investigation |
| Host/container dependency checks | PASS |
| Supplied smoke on fresh Windows candidate | PASS |
| Supplied smoke against/inside fresh container | PASS / PASS |
| Existing full-catalog proxies | 37/37, no regression |
| Existing native advanced checks | 20/20; four are unsupported-request safety checks |
| New frozen development proxies | 16/25 before → 25/25 after |
| New held-out proxies | 7/14 before → 13/14 after |
| New native MCP checks | 38/39 on Windows and Linux; all 39 payloads identical across platforms |
| Exact-page native workload | 300/300 correct before and 300/300 after, zero errors |
| Candidate source/container identity | All 16 checked source/test/evaluation/config files and catalog byte-identical |
| Disposable container | Healthy, UID inherited 10001, 1 GiB / 1 CPU test limit; stop exit 0, no OOM; removed |

The new 39 cases were frozen before parser changes: 25 development and 14 held out.
They cover unrelated grammar, money/rating/review/result units, colors/patterns,
audiences, mixed scopes, complements, explicit exclusions, unsupported facts and
impossible requests. Development cases drove the changes; held-out responses were
not used for a second tuning round. The exact calibrated case-file SHA-256 is
`4489cfd3e012f89c0bb266e087b301deb4bfc5bdd56de827a9268f1654cdc39b`.

One proposed development expectation was corrected **before application edits**:
catalog review counts are 0–8, so a positive 100-review case had no candidates.
The calibrated comparison uses at least five reviews. The initial exploratory
15/25 report is not substituted for the comparable 16/25 baseline. A held-out
floral expectation was defined by literal source text rather than inventing a
`Floral` pattern field before tuning began.

The retained held-out stress failure is `floral skirt with coordinating bag under
1500`: one primary and five recommendations are returned. The catalog contains
only **one Skirt with literal `floral` evidence**; the evaluator's ten-primary-slot
stress requirement is not met. This is a conservative lexical-recall/slot-coverage
limit, not an invalid ID or budget relaxation. The test was not weakened after
observing its failure, and no speculative replacement products were added. Broader
flower/pattern concepts need separately reviewed evidence and new held-out cases.

These evaluators grade attributes and coverage; they do **not** establish Bedrock
grades, occasion suitability, style quality, complement judgments or an official
score. They also report counts/per-case failures rather than serving as an automatic
release approval; the known 38/39 result must not be called an all-green quality pass.
Owned-item outfit context still returns empty arrays, and no native basket/outfit
planner or total-budget claim is introduced. Combined basket budgets are outside v1.

Latency was measured using the existing fixed 50-call local pool, 20 warmups,
concurrency 1 then 5, three repetitions, 300 timed calls per version:

| Local version | Correct | p50 | nearest-rank p95 |
|---|---:|---:|---:|
| Preserved pre-quality candidate, port 8031 | 300/300 | 30.44 ms | 113.36 ms |
| Fresh quality candidate, port 8035 | 300/300 | 31.69 ms | 118.16 ms |

Pool SHA: `dc7b51d5ca0a9f8ec8316fc2dc543326defe206e4920c77eaf5f8a090772aefd`.
This is a single paired localhost comparison, not evidence of a significant speed
change. The exact-page implementation was unchanged. The full-catalog direct proxy
run measured 4.58 s load/index time and 651.34 MiB peak process memory. This excludes
full deployment cold-start conditions and is not a hosting SLA. Public Run #14's
measured p95 is 1600 ms; no public speed improvement is claimed from local timings.

Portable before/after reports and current source hashes are in
`evaluation/reports/quality-{before,after}-{dev,heldout}.json` and
`evaluation/reports/quality-checks.json`. Earlier remediation manifests are historical:
their old `query.py` hash is not the new candidate's hash. Final documentation was
written after the image build; the image/source identity claim covers the checked
runtime/test/evaluation/config set, not post-build documentation.

The preserved committed-release export differed from Git blobs by CRLF/LF only
in the eight inspected source/config files; content matched after LF normalization.
Do not describe that export as byte-identical to Git. The frozen catalog hash and
current container/source byte checks were verified independently.

## 4. Score-oriented priorities and uncertainty

Official rules are in `hackathon-brief.md`; scores below are Run #14 observations,
not estimates for this candidate.

| Rubric | Weight / Run #14 | Evidence and next quality gate |
|---|---|---|
| Validity/constraints | 25 / 25 | Preserve exact schemas, original string IDs, filter precedence, sort/null/tie/page/error behavior. Unit/smoke/exact-page checks pass; deployed future artifact still needs verification |
| Ranking | 30 / 0 | Public natural-language retrieval empty on probes, local engine nonempty. Broader attribute ranking checks improved 4/13 → 13/13; semantic grade-3 relevance remains unmeasured |
| Meaningful unusual | 7.5 / 1.5 | Broader unusual proxies 2/5 → 5/5; unknown natural wording can still cause strict lexical abstention. Need independent catalog-based semantic review |
| Irrelevant/impossible | 7.5 / 7.5 | New negatives 10/10 before/after; preserve rejection rather than broadening every request |
| Mixed choices | 15 / 0 | Broader mixed coverage 3/5 → 5/5; scopes/quantities/duplicate IDs tested. Coverage proxies do not prove Bedrock nDCG |
| Recommendations | 10 / 0 | Four-query local comparison returns five real complements; broader checks 2/3 before/after, with retained primary-slot stress failure. Styling and cross-product compatibility remain heuristic |
| Performance | 5 / 0 | Requires functional ≥85.5/95 and workload correctness ≥95%. Local 300/300 does not establish public latency or eligibility |

The formula is `5 × correct_rate × clamp((2000 − p95_ms)/1800, 0, 1)` after
eligibility. Conditional arithmetic scenarios, **not score forecasts**:

| Assumed functional points | Assumed p95 / correctness | Conditional total |
|---:|---|---:|
| 85.5 | ≤200 ms / 100% | 90.50 |
| 90 | 1600 ms / 100% | 91.11 |
| 88 | 800 ms / 100% | 91.33 |

Merely crossing eligibility cannot achieve 91. Maximizing the chance of exceeding
91 needs both high semantic functional quality and verified target-host latency.
No defensible probability or expected official score can be assigned from these
proxy samples.

Prioritized experiments and release work:

1. **Release parity first.** Confirm the hosting source repository/ref/built SHA,
   then publish only an explicitly reviewed immutable candidate after authorization.
   Acceptance: runtime identity plus smoke and broad public/local response checks.
   Highest expected practical benefit; small implementation cost, deployment risk
   controlled by recording rollback artifact and avoiding uncontrolled auto-deploy.
2. **Measured parser repair (implemented).** Low-complexity deterministic grammar,
   units and aliases; no ranking rewrite or new service. Dev/held-out evidence above
   supports retaining the patch, with conservative unknown-term handling preserved.
3. **Independent semantic review before semantic machinery.** Review new catalog-
   grounded ranking, unusual, mixed and complement requests with relevance grades
   recorded independently of the implementation; reserve a fresh held-out set.
   Investigate conceptual recall and complement styling using those labels. Add
   semantic retrieval or reranking only if it beats the lexical baseline with hard
   filters and acceptable latency. This is unmeasured future work, not an assumed gain.

Do not optimize empty-query speed first while semantic functional points are the
main loss. No new ranking architecture is justified by Run #14 until the actual
reviewed code is deployed and evaluated independently.

## 5. Exact files and proposed release procedure

The candidate inherits the entire committed release at `2dd37a2`. Existing changes
remain four tracked files and eight untracked project files from the prior sprint.
This quality work changes only `query.py` and appends README documentation; it adds
the five quality evaluator/test files, five portable evidence files and this report.

Proposed **23-file** change list relative to HEAD (nothing staged):

```text
README.md
query.py
recommendations.py
search.py
docs/PUBLIC_DEPLOYMENT_FIX.md
docs/REMEDIATION_REPORT.md
docs/QUALITY_RELEASE_PLAN.md
evaluation/advanced.py
evaluation/advanced_cases.json
evaluation/quality.py
evaluation/quality_cases.json
evaluation/quality_mcp.py
evaluation/reports/remediation-checks.json
evaluation/reports/remediation-native-before.json
evaluation/reports/remediation-native-after.json
evaluation/reports/quality-checks.json
evaluation/reports/quality-before-dev.json
evaluation/reports/quality-after-dev.json
evaluation/reports/quality-before-heldout.json
evaluation/reports/quality-after-heldout.json
tests/test_remediation.py
tests/test_quality.py
tests/test_transport_security.py
```

Review historical report status statements as historical, not current assertions.
Ignored `.audit-tmp/` profiling, backups, logs and temporary scripts are excluded.
No secret or credential is required in any release file. Server, Dockerfile,
dependency pins, supplied smoke, schemas and catalog are unchanged against HEAD.
Catalog SHA: `05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073`.

**Do not execute the following publishing steps without fresh authorization.**

- Confirm the actual hosting GitHub repo/ref and last built commit from its build
  record. Record the current public rollback image/revision. Determine whether a
  push automatically deploys; coordinate push and rollout authorization accordingly.
- Review/stage exactly the allowlist above, run `git diff --cached --check`, review
  `git diff --cached`, and create a new commit. Proposed message:
  `fix: improve grounded Polaris query interpretation`. Record the resulting full
  SHA; one cannot be supplied before a commit is authorized and made.
- Verify a clean isolated checkout of that SHA, materialize the official LFS object,
  check its checksum and build the Docker image. Do not build a Git-only release
  from starter `origin/main` or an arbitrary dirty directory. Keep one worker and
  preserve the currently functioning exact Host allowlist and Origin validation.
- After authorization, `git push origin main:main` is the expected normal
  fast-forward publication **only if** the hosting repository/ref is confirmed to
  match. No force push or upstream push. Pin the actual new SHA in the deployment
  and confirm build/boot logs; do not invent SpringWinter CLI commands.
- Verify public `/healthz`, MCP revision/schema/smoke, the four exact queries and
  broader `quality_mcp.py` results against the pinned local version. Investigate
  divergences rather than immediately buying another official attempt. Measure
  public exact-page latency separately and confirm Host rejections are absent for
  legitimate requests. No official attempt until separately authorized.

Using existing commit `2dd37a2` would be a smaller emergency recovery and already
fixes the four observed empty-result probes, but **omits the later remediation and
quality fixes**. It must not be represented as the intended latest candidate.

## 6. Commands executed / reproducible checks

Commands were run from the repository root in PowerShell unless noted. Host async,
network, Git LFS status and Docker checks used the approved external environment.

```powershell
git --no-optional-locks status --short --untracked-files=all
git rev-parse HEAD
git branch -avv
git remote -v
git ls-remote --heads origin main
git diff -- README.md query.py recommendations.py search.py
git diff --cached --stat
git diff --check
git diff --exit-code HEAD -- server.py Dockerfile requirements.txt schemas data/products.json smoke_test.py

.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe evaluation/run.py --split all --output .audit-tmp/quality-original-proxies.json
.\.venv\Scripts\python.exe evaluation/quality.py --split dev --output .audit-tmp/quality-after-dev.json
.\.venv\Scripts\python.exe evaluation/quality.py --split heldout --output .audit-tmp/quality-after-heldout.json
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8035/mcp
.\.venv\Scripts\python.exe evaluation/quality_mcp.py http://127.0.0.1:8035/mcp --output .audit-tmp/quality-native.json
.\.venv\Scripts\python.exe evaluation/advanced.py http://127.0.0.1:8035/mcp --output .audit-tmp/quality-advanced.json
.\.venv\Scripts\python.exe evaluation/mcp_check.py http://127.0.0.1:8031/mcp --output .audit-tmp/quality-latency-before.json
.\.venv\Scripts\python.exe evaluation/mcp_check.py http://127.0.0.1:8035/mcp --output .audit-tmp/quality-latency-after.json

docker build -t polaris-search:quality-candidate .
docker run --rm --network none polaris-search:quality-candidate python -m unittest discover -s tests -v
docker run --rm --network none polaris-search:quality-candidate python -m pip check
docker run -d --name polaris-quality-check --memory=1g --cpus=1 -p 127.0.0.1:8036:8000 polaris-search:quality-candidate
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8036/mcp
docker exec polaris-quality-check python smoke_test.py http://127.0.0.1:8000/mcp
.\.venv\Scripts\python.exe evaluation/quality_mcp.py http://127.0.0.1:8036/mcp --output .audit-tmp/quality-container-native.json
docker inspect polaris-quality-check --format '{{json .State.Health}}'
docker image inspect polaris-search:quality-candidate --format '{{.Id}}'
docker stop --time 10 polaris-quality-check
docker inspect polaris-quality-check --format 'Exit={{.State.ExitCode}} OOM={{.State.OOMKilled}}'
docker rm polaris-quality-check

.\.venv\Scripts\python.exe .audit-tmp/quality-public-comparison.py
```

The fresh Windows candidate was launched with `python server.py` through hidden
`Start-Process`, process-local `HOST=127.0.0.1`, `PORT=8035`, `WEB_CONCURRENCY=1`,
and the existing loopback-plus-exact-public-host `MCP_ALLOWED_HOSTS` value. It remains
available on `http://127.0.0.1:8035/mcp`. Older servers on 8000, 8031 and 8033 remain
preserved. Temporary container 8036 was removed. Direct baseline quality runs used
the frozen pre-edit modules in an isolated Python process; report hashes identify
the old sources. Original Run #14 evidence was not overwritten. Fresh comparisons
are in `.audit-tmp/release-investigation-comparison.json` and
`.audit-tmp/quality-public-comparison.json`.

**Single highest-value next action:** open the actual SpringWinter **web-service
hosting/build page where GitHub was connected** and provide its connected repository,
branch and last built commit/image. The Run #14 scorecard is not that page. This
resolves the release blocker before authorizing capture/publication of this candidate.
