# Deployment readiness audit — 21 October 2026

**Overall: BLOCKED for a reproducible, platform-verified deployment; PASS for the
tested local single-process container.** No application code was changed. No
deployment, publication, AWS provisioning, IAM changes, push or official benchmark
attempt occurred. Existing working-tree changes were preserved.

## 1. Scope and release identity

Read `docs/AUDIT.md`, `docs/REPORT.md`, `AGENT.md`, the complete
`hackathon-brief.md` including scoring and schema appendices, both schemas,
`server.py`, `search.py`, `query.py`, `recommendations.py`, `Dockerfile`,
`requirements.txt`, README/configuration/ignore files, all seven test modules,
`smoke_test.py`, and the local evaluation programs and results.

| Item | Verified evidence |
|---|---|
| Branch | `main` |
| HEAD | `e1cbc5fe8d4831719c530309075cccea2a278401` |
| Tracked changes, normal LFS-aware status | `.dockerignore`, `.gitignore`, `README.md`, `search.py`, `server.py`, `tests/test_search.py` — six modified files, none staged |
| Untracked files before this report | 28: `docs/AUDIT.md`, `docs/REPORT.md`; `query.py`, `recommendations.py`; six new test modules; `evaluation/cases.json`, `evaluation/run.py`, `evaluation/mcp_check.py`, and 15 `evaluation/reports/*.json` files |
| This audit's deliverable | Adds this report; diagnostic helpers/logs remain in ignored `.audit-tmp/` |
| Existing source manifest | Every file/hash in `evaluation/reports/final-sources.json` still matches, including runtime code, schemas, Dockerfile, requirements and evaluation programs |
| Tested local image | `polaris-search:readiness`, image ID `sha256:efab9612e856d40023c69731003420e3eeaa9f67902696176ee1455396d4efc7`, Linux amd64 |

**FAIL — release snapshot:** HEAD contains the starter, not the current tested
implementation. In particular, `query.py`, `recommendations.py`, the expanded tests
and evaluation files are untracked. A Git-based build of this HEAD would deploy
different search and GET behavior. Preserve and review these changes, then capture
an explicit release commit/artifact before a Git-based deployment. Nothing was
staged, committed, reset or discarded during this audit.

Normal `git --no-optional-locks status --short` was rerun outside the Windows sandbox
and correctly shows **no catalog modification**. The sandbox workaround that disables
LFS filters reports materialized JSON versus its pointer as modified; that is an
inspection artifact, not a reason to replace or recommit the catalog.

## 2. Current verification results

All results below were rerun during this audit; earlier report numbers are not
being substituted for new test execution.

| Check | Status | Evidence |
|---|---|---|
| Host unit suite, Python 3.14 virtual environment | PASS | 34/34 methods; 0.124 s in the recorded verbose run |
| Host dependency consistency | PASS | `pip check`: no broken requirements |
| Clean Docker dependency installation | PASS | `docker build --no-cache`; pinned requirements downloaded and installed |
| Container unit suite, Python 3.12 | PASS | 34/34 methods; 0.106 s |
| Container dependency consistency | PASS | `pip check`: no broken requirements |
| Official supplied smoke client from host | PASS | Initialization, revision, exact tool/schema discovery, structured/text output, valid calls and invalid-argument errors |
| Official supplied smoke client inside container | PASS | Same checks against container loopback |
| Existing full-catalog local evaluation | PASS, proxy only | 37/37; no tuning or application edits performed |
| Real MCP exact-page workload | PASS, local only | 300/300 correct, zero errors, median 45.19 ms, nearest-rank p95 124.92 ms |
| Real MCP pagination and repeat probes | PASS | Empty-query rating ascending, black-dress price descending, and mixed relevance; offset 9 / limit 7 equals larger prefix slice and repeated page |
| Valid unknown filter with recommendations enabled | PASS | Both arrays empty, successful tool response |
| Official hidden/Bedrock benchmark | BLOCKED / NOT RUN | Not authorized; no official score or eligibility result exists |

The unit suite includes **240 exact-page fixture combinations** covering eight
filter sets, five sorts, both directions and three offsets. The real MCP workload
adds full-catalog exact pages but uses offset zero; the separate real pagination
probes above cover nonzero pages. These checks do not prove every possible query.

## 3. Docker, configuration and lifecycle

### Startup and binding

- Docker runs `python server.py` directly as PID 1, UID **10001**. No shell wrapper
  interferes with signal delivery. Default binding is **0.0.0.0:8000**; host access
  through the published container port confirms it is not container-loopback-only.
- `PORT=8080` was separately tested with host mapping `127.0.0.1:8028:8080`.
  MCP initialization and health both pass. `EXPOSE 8000` is image metadata; the
  actual runtime port, health URL and platform forwarding must agree.
- Tests published ports only on host loopback. Nothing was made publicly reachable.
- Under an explicit local limit of **1 GiB RAM / 1 CPU**, launch-to-first-successful
  `/healthz` took **9.54 s** on port 8000 and **8.26 s** on port 8080. These include
  Docker CLI/container launch, Python imports, catalog/index construction and health
  polling. They are diagnostic samples, not a cold-start SLA.
- ASGI lifespan loads the catalog and constructs the index before Uvicorn completes
  startup. Before readiness, health polling saw connection failures, rather than an
  early misleading 200 or a served 503. A deployment needs startup grace.
- Missing `CATALOG_PATH=/app/data/missing-readiness.json` fails startup with exit
  **3** and `FileNotFoundError`; there is no silent fallback to an empty catalog.

### Transport and ingress

| Probe | Default configuration | With exact synthetic host allowlist |
|---|---:|---:|
| Initialize on loopback | 200, `application/json` | 200 |
| Negotiated MCP revision | `2025-11-25` | `2025-11-25` |
| Session header | absent; stateless manager | absent |
| GET /mcp, HEAD /mcp | 405 | 405 |
| Ordinary REST-style POST with search arguments | 400 | 400 |
| GET /healthz | 200, `{"status":"ok","products":105126}` | 200 |
| GET / | 404 | 404 |
| Initialize with `Host: audit.example.invalid` | **421** | **200** |
| Initialize with unapproved Origin | **403** | **403** |

The manager is the pinned official MCP SDK, with `json_response=True` and
`stateless=True`. The supplied smoke client verifies exactly one `search_products`
tool, exact input/output schemas, and matching JSON text plus `structuredContent`.
Malformed arguments produce accepted MCP tool errors, not fabricated empty success.
No SSE connection or session affinity is required for these tested calls.

**Required deployment configuration:** allow the actual public Host value, including
any port form preserved by the proxy, in `MCP_ALLOWED_HOSTS`; retain loopback entries.
Add an exact allowed Origin only if the actual caller/proxy requires one. Do not
disable transport security or add an unrestricted wildcard to work around this.
The synthetic Host test changes a local HTTP header only; it is not a test of public
DNS, TLS, routing, organizer reachability or SpringWinter infrastructure.

### Health and shutdown

- Docker health command uses `127.0.0.1:$PORT/healthz`, including the overridden
  port. Its configured interval is **30 s**, timeout **5 s**, start period **60 s**,
  retries **3**; the inner urllib timeout is **3 s**. Both explicit health commands
  returned 200. The running default container became **healthy**, with zero failing
  streak and repeated Docker probe exit codes of zero.
- Health means catalog loading completed and the process can answer the route.
  It checks product count, not the catalog SHA or search correctness. The separate
  integrity and MCP probes remain necessary for release verification.
- `docker stop --time 10` completed normally for both ports. Each logged
  `Application shutdown complete` and `Finished server process`, exited **0**, and
  was not OOM-killed. Stop plus inspection/log collection took about **3.02 s** and
  **3.28 s**. A stopped container's health field is not a running-readiness result.
- These were normal shutdowns after calls completed. Cancellation during catalog
  loading, draining a long in-flight search, crashes, restarts and rolling replacement
  were **not** stress-tested. No explicit server request deadline or graceful-drain
  deadline is configured. A benchmark client timeout does not itself stop CPU work
  in the AnyIO worker thread. The platform's termination grace needs confirmation.

### One-worker configuration trap

**Reproduced conditional startup failure:** `WEB_CONCURRENCY=2` causes this entry
point to exit **3**, with Uvicorn's warning that workers/reload require an import
string. The code passes the app object to `uvicorn.run`.

**Smallest remedy:** keep the current entry point and explicitly configure
`WEB_CONCURRENCY=1` if the hosting platform injects a worker setting. No application
rewrite is required for the tested deployment mode. If multiple workers are later
required, first review an import-string entry point and measure duplicated catalog
memory; do not assume workers share the index.

## 4. Catalog and protocol invariants

The built image loads `/app/data/products.json` by default. It contains **105,126
unique IDs**, all strings; **all 105,126 start with a zero**. The host and profile
confirm the official **106,498,333-byte** file and SHA-256:

```text
05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073
```

`git show HEAD:data/products.json` is the matching Git LFS pointer. A fresh CI clone
must materialize LFS before the Docker build; building a pointer would not produce
a usable catalog. CI/LFS fetch permissions, quota and availability are unverified.

Source review and executed checks confirm:

- Original string IDs flow through postings, lookup, primary results and recommendation
  references without integer conversion. Returned facts/IDs come from the catalog.
- Explicit string filters use trimmed, case-insensitive **exact** catalog values;
  numeric bounds are inclusive; filters combine with AND. Null ratings fail a
  minimum-rating filter, and no-review products pass minimum review count zero.
- Empty/whitespace queries use exact, preordered catalog scans. There is no ANN
  truncation. Price/rating/review-count ties retain ascending IDs in either direction;
  null ratings are last. Offset follows filtering/ordering. Repeated requests and
  tested pages are deterministic.
- Nonempty queries select candidates before field sorting. Mixed relevance uses
  per-branch ranks with one shared limit. Recommendations are unique, disjoint from
  primary IDs, capped at five, and reference a primary on the current page.
- Both arrays are returned for valid requests. Invalid property/type/range cases,
  blank filters, null arguments, nonfinite direct-Python numbers and reversed price
  bounds are covered by validation tests; MCP invalid-call behavior passes smoke.
- Schemas, requirements and Dockerfile are unchanged relative to HEAD; runtime
  hashes match the preceding report's source manifest. The protocol revision was
  negotiated and verified with the installed SDK, not inferred from a comment.

The server does not independently reject a different valid catalog supplied through
`CATALOG_PATH`, nor verify its SHA on startup. Keep that setting unset for the bundled
catalog, or validate any mounted file against the official digest before release.
The inspected runtime uses no AWS/model credentials or external product service.
No credentials were added or exposed. This audit is not a comprehensive secret or
dependency-vulnerability scan.

## 5. Full-catalog performance and resource review

New isolated direct-Python profile, **1 GiB / 1 CPU**, original catalog:

| Measurement | Observed |
|---|---:|
| Catalog load + index construction, excluding server startup | 5.41 s |
| Process peak RSS after construction | 637.38 MiB |
| Vocabulary / postings memberships | 15,402 / 3,488,660 |
| Precomputed ordered catalog lists | 8 |
| Default exact page | 0.17 ms |
| Unsatisfiable numeric filter, offset 10,000 | 85.13 ms |
| `cotton`, limit 100 | 361.98 ms |
| Five mixed product choices, limit 100, recommendations on | 1,505.47 ms |
| Dress + matching bag, offset 10,000, limit 100 | 130.62 ms |
| 1,000-character nonsense query | 6.71 ms; empty arrays |
| Process peak RSS after these samples | 648.21 MiB |
| Server container snapshot after the MCP workload | 697.9 MiB / 1 GiB |

These samples passed ID uniqueness, known-ID and recommendation-reference checks;
they are not semantic relevance grades. RSS includes the catalog, index, interpreter
and temporary allocations, not just index storage. Docker memory is a different
container metric. The full decoded JSON retains synthetic reviews even though search
does not use them as factual retrieval evidence. Eight sort lists hold references,
not eight deep copies of product records.

The new real MCP workload used the existing 50-request pool, 20 warmups and 300 timed
calls, concurrency 1 then 5 repeated three times, with exact-page oracle checks:
**300 correct, 0 errors, p50 45.19 ms, p95 124.92 ms**. Correct throughput was
34.06–40.67 requests/s at concurrency 1 and 53.27–60.61 at concurrency 5. Pool SHA:
`dc7b51d5ca0a9f8ec8316fc2dc543326defe206e4920c77eaf5f8a090772aefd`.

Limits and unmeasured assumptions:

1. One successful 1 GiB scenario is not a proven minimum or a sizing guarantee.
   Start with the README's approximate 2 GB headroom if the eventual platform allows
   it, then measure its actual memory limit, CPU allocation and concurrency. No paid
   capacity was provisioned to make that recommendation.
2. The index and eight sort orders rebuild once per process start; no persistent
   lexical index is loaded. Slower CPUs, constrained disk, image pulls and LFS
   materialization can add cold-start time. No startup distribution or ARM64 build
   was measured. The base tag `python:3.12-slim` is mutable; the tested build resolved
   `sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2`.
3. Exact empty-query requests are much cheaper than broad relevance/recommendation
   requests. The 300-call performance pool does not measure semantic concurrency.
   Sustained broad-query concurrency, maximum worker-thread pressure, memory growth,
   health responsiveness under saturation and long-duration soak behavior remain
   unmeasured. Threads protect the event loop but do not remove Python CPU costs.
4. Runtime has no model download, image fetch, embedding service or database. Builds
   require package-registry/base-image access. Pins installed cleanly, but package
   hashes and the Docker base digest are not locked in source.

## 6. Review against official scoring

| Official area | New local evidence | Remaining uncertainty |
|---|---|---|
| Validity / constraints — 25 | 34 test methods, exact fixture pages, actual MCP schemas/errors, 300 exact pages and repeat/pagination probes pass | Hidden validity suite not run; natural-language parsing is rule-based, not an exhaustive hard-requirement proof |
| Ranking — 30 | 8 local ranking cases pass; lexical field/IDF/phrase evidence present | Rule grades are 0/3 catalog predicates, not live Bedrock 0–3 relevance judgments; no official nDCG measured |
| Unusual / irrelevant — 15 | 9 local cases pass, including six empty-response cases | Unknown terms remain hard requirements; meaningful paraphrases can be rejected. The raw aggregate proxy nDCG includes non-ranking zeros and is not this official score |
| Mixed choices — 15 | 5 local cases pass; pooled branch ranking and shared limit; repeat pagination passes | No semantic style/choice judgments; similar catalog variants can occupy many slots. Branch balancing does not guarantee overall fashion diversity |
| Complements — 10 | 4 local cases plus scope/reference tests pass; reviewed category compatibility, audience and accessory budgets | Compatibility, color coordination and audience inference remain heuristics. A useful complement and a sufficiently relevant referenced primary still need Bedrock judgment |
| Performance — 5 | Local exact workload p95 124.92 ms, 100% correct | No official pool, network or functional eligibility measurement |

The rerun's **37/37 is a local regression/proxy result**, not a benchmark pass.
Previously held-out cases have already been consumed. Preserve a fresh independent
set before future tuning. The official functional suite has 100 cases and performance
credit requires **at least 85.5/95 functional points** and **95% correct performance
calls**. No functional score or performance points can be claimed here. Ten-second
ordinary call and thirty-second connection/discovery deadlines are organizer limits,
not guarantees established by these samples. An official attempt must remain a
separately authorized action.

## 7. SpringWinter compatibility: verified versus unknown

Authoritative competition sources are the supplied brief and
[official starter repository](https://github.com/SpringWinter-Research/Polaris-Hackathon-Base-MCP).
The brief describes a SpringWinter account/submission flow and a reachable HTTP
`/mcp` endpoint, while allowing teams to choose hosting/AWS resources. It does
**not** specify a SpringWinter container-hosting runtime. Public repository/web
inspection did not establish an authoritative hosting contract. This is a lack of
verified information, not a claim that no such service or private instructions exist.

Verified: generic Docker startup, configurable integer `PORT`, 0.0.0.0 binding,
configurable MCP Host/Origin allowlists, JSON Streamable HTTP, `/healthz`, and normal
single-process shutdown work locally. No SpringWinter-specific deployment manifest
is present in the inspected workspace. There is no verified deployed URL.

**BLOCKED pending confirmation from the actual hosting/organizer configuration:**

- Whether SpringWinter is only the submission portal or also the intended runtime;
  the actual hosting target and expected build/start command.
- Required internal port or injected variable, public hostname/Host header, path
  prefix/rewrite, TLS termination and proxy preservation of MCP headers/JSON bodies.
- Probe method/path, whether Docker HEALTHCHECK is honored, startup grace, readiness
  versus liveness behavior, idle suspension and cold-start policy. `/` currently
  returns 404; `/mcp` GET returns 405 and must not be assumed to be a health URL.
- CPU/RAM/architecture, replica or worker injection (especially WEB_CONCURRENCY),
  termination/drain grace, request/body/connection timeouts and build network access.
- Git LFS checkout behavior if deployment builds from the fork; artifact/image
  acceptance and immutable release identification.
- Organizer runner region/source IP, allowed ingress and evaluation window.

A candidate environment, **only after substituting confirmed values**, is:

```text
HOST=0.0.0.0
PORT=<confirmed internal port>
WEB_CONCURRENCY=1
MCP_ALLOWED_HOSTS=localhost:*,127.0.0.1:*,[::1]:*,<confirmed public hostname>,<confirmed public hostname>:*
# Keep CATALOG_PATH unset for the bundled official catalog.
# Set exact MCP_ALLOWED_ORIGINS only if the confirmed caller sends Origin.
# Configure GET /healthz as the probe only if the platform supports that setting.
```

These are proposed settings, not changes applied to a platform or proof of its
requirements. Public DNS/proxy/runner checks require a later authorized deployment.

## 8. Exact commands and audit evidence

Commands were executed from the workspace root in PowerShell. Docker/network and
async host checks ran outside the Windows sandbox where necessary; no source was
escalated into a deployment.

```powershell
git branch --show-current
git rev-parse HEAD
git --no-optional-locks status --short
git ls-tree -r --name-only HEAD
git ls-files --others --exclude-standard
git show HEAD:data/products.json
git diff --exit-code -- schemas requirements.txt Dockerfile
Get-FileHash data/products.json -Algorithm SHA256

.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
docker version
docker build --no-cache -t polaris-search:readiness .
docker run --rm polaris-search:readiness python -m unittest discover -s tests -v
docker run --rm polaris-search:readiness python -m pip check

# Default local-only runtime; the audit helper timed polling from before docker run.
docker run -d --name polaris-readiness-default --memory=1g --cpus=1 -p 127.0.0.1:8027:8000 polaris-search:readiness
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8027/mcp
docker exec polaris-readiness-default python smoke_test.py http://127.0.0.1:8000/mcp
.\.venv\Scripts\python.exe evaluation/mcp_check.py http://127.0.0.1:8027/mcp --output .audit-tmp/readiness-mcp.json
docker inspect --format '{{json .State.Health}}' polaris-readiness-default
docker stats --no-stream polaris-readiness-default

# Alternate-port scenario, also created by the audit helper.
docker run -d --name polaris-readiness-port --memory=1g --cpus=1 -p 127.0.0.1:8028:8080 -e PORT=8080 -e 'MCP_ALLOWED_HOSTS=localhost:*,127.0.0.1:*,audit.example.invalid,audit.example.invalid:*' polaris-search:readiness

# Deliberate negative startup scenarios: both exit 3; not normal startup commands.
docker run --rm -e WEB_CONCURRENCY=2 polaris-search:readiness
docker run --rm -e CATALOG_PATH=/app/data/missing-readiness.json polaris-search:readiness

# Cleanup performed for each audit server, preserving the local image.
docker stop --time 10 polaris-readiness-port
docker rm polaris-readiness-port
docker stop --time 10 polaris-readiness-default
docker rm polaris-readiness-default
```

Audit-specific helpers were written only into ignored `.audit-tmp/`:
`readiness_probe.py` (`start`, `alternate`, `stop`) performed the displayed Docker
launch/stop commands, HTTP header probes, readiness timing and lifecycle recording;
`readiness_profile.py` performed the direct profile. The exact additional profile/
evaluation commands were:

```powershell
$taskRoot=(Get-Location).Path
docker run --rm --memory=1g --cpus=1 --mount "type=bind,source=$taskRoot\.audit-tmp,target=/app/.audit-tmp" polaris-search:readiness python .audit-tmp/readiness_profile.py
docker run --rm --mount "type=bind,source=$taskRoot\.audit-tmp,target=/app/.audit-tmp" polaris-search:readiness python evaluation/run.py --split all --output .audit-tmp/readiness-eval.json
```

Raw scratch evidence: `readiness-build.log`, `readiness-runtime.json`,
`readiness-negative-startup.json`, `readiness-profile.json`, `readiness-eval.json`,
`readiness-mcp.json`, `readiness-pagination.json`, `readiness-git.json`, and per-server
logs. These ignored diagnostics are not part of a fresh clone; the material findings,
metrics and commands are preserved in this report. Both named audit servers were
stopped and removed. Existing source files and historical evaluation reports were
not rewritten.

## 9. Prioritized remediation plan and decision

| Priority | Action | Smallest change / acceptance evidence |
|---|---|---|
| P0 | Capture a reviewed, reproducible release snapshot | Include modified runtime files and required untracked files; preserve catalog LFS identity. Verify a clean checkout of that snapshot builds and passes tests/smoke. Do not deploy starter HEAD accidentally |
| P0 | Obtain the actual hosting contract and organizer ingress details | Resolve Section 7; configure confirmed port, `/healthz` support, exact Host allowlist, one worker, CPU/RAM and startup/drain grace. No speculative application rewrite |
| P1 | Validate the release under target-equivalent resources | Repeat clean build, SHA, readiness, smoke and exact workload; add broad-query concurrency and shutdown-during-request checks if required by the target |
| P1 | Establish semantic readiness independently | Fresh judged ranking/mixed/complement/irrelevant queries; keep proxies separate from Bedrock. No unauthorized official attempt |
| P2 | Harden release reproducibility if needed | Pin the tested base digest and package hashes; add artifact checksum/LFS preflight in the release workflow. Optional, not a demonstrated local runtime failure |

- **PASS:** existing code preserved; host/container tests, clean dependency install,
  official public smoke, catalog integrity, tested protocol/filter/sort/page/error
  invariants, health, alternate port, normal shutdown and local resource checks.
- **FAIL:** a reproducible release of the tested implementation is not captured in
  committed HEAD; a Git-based deployment of this HEAD would use the starter.
- **BLOCKED:** SpringWinter/hosting requirements and organizer reachability are
  unverified; official benchmark/Bedrock score has not been run.

**Single highest-priority next action:** review and capture the current working tree
as an explicit release snapshot, including required untracked implementation files,
before any Git-based deployment. This audit does not perform that commit or deploy it.
