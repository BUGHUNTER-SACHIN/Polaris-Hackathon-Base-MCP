# Public MCP incident and prepared fix — 21 October 2026

Status: **public MCP FAIL; minimal fix verified locally; rollout BLOCKED pending
deployment access and explicit authorization.** No push, commit, public setting
change, deployment or official benchmark was performed during this investigation.

## Confirmed cause and evidence

The public service responds to GET `/healthz` with HTTP 200 and
`{"status":"ok","products":105126}`. An MCP initialize POST with no Origin
returns HTTP 421 and `Invalid Host header`. The supplied public smoke client fails
with the same status. The immediate blocker is MCP Host validation, before tool
execution. Health does not establish search functionality or deployed source identity.

The authenticated [Run #5 results page](https://admin-dashboard.01m5erq7wn81nf6mhfpqkjb0ka.apps.springwinter.dev/runs/5)
was inspected: overall 0/100; Validity, Ranking, Unusual, Irrelevant, Mixed,
Recommendation and Performance all zero; **0/100 cases evaluated, zero timed calls**,
functional score 0/95 and p95 displayed as 10000 ms. That p95 is not a measured
search latency established by this run. The team dashboard displays four of five
attempts remaining and one listed run (#5); do not infer attempts used from the run ID.
No benchmark submission control was used.

`server.py` reads `MCP_ALLOWED_HOSTS` at module import, splits on commas, strips
whitespace and removes empty entries. Its default permits loopback only. It passes
these settings to the installed MCP SDK 1.30.0 session manager. The SDK checks Host
before Origin, accepts exact hostnames and hostname-with-port patterns ending in
`:*`, rejects invalid Hosts with 421 and invalid Origins with 403. Missing Origin
is accepted. A restart is required after an environment change. Host validation
remains enabled; no Origin change is supported by the current evidence.

The exact Host received behind the public proxy is **not established from server
logs**: no deployment-management/logs page has been supplied. The request we sent
targets the public hostname below. A proxy rewrite to another Host remains an
unresolved possibility; inspect the log's `Invalid Host header: ...` value before
expanding this allowlist. The benchmark dashboard has no deployment/log links.

## Prepared configuration (not applied publicly)

Set this environment variable on the actual running web service, then restart it
only after authorization:

```text
MCP_ALLOWED_HOSTS=localhost:*,127.0.0.1:*,[::1]:*,web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev,web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev:*
```

No application patch is necessary in the inspected source. Do not replace this
with a blanket wildcard or disable middleware. Leave `MCP_ALLOWED_ORIGINS`
unchanged. If logs show a different legitimate upstream Host, allow only that
confirmed name. Confirm the deployed source supports this variable before relying
on it; its actual revision is not yet verified.

Keep one worker. Existing Docker startup is `python server.py`, binding to
`HOST` (default `0.0.0.0`) and integer `PORT` (default `8000`). The image includes
GET `/healthz` checks. Platform port, injected worker settings, probe and startup
grace must be read from deployment configuration rather than assumed. Catalog
loading/index construction precedes application readiness.

## Release identity and preserved changes

- Branch: `main`; local HEAD: `2dd37a2a63377074f3f909a9bff1f2e489def570`.
- Runtime release: `689e11b7e26d996e8615edaf0c854ebb8c244176`; the later HEAD
  adds strategy documentation, with identical runtime code.
- Live `git ls-remote --heads origin main`:
  `e1cbc5fe8d4831719c530309075cccea2a278401` (starter). A deployment building that
  ref would miss the reviewed runtime and parsing fixes. Do not deploy it.
- Public OPTIONS previously advertised HEAD/GET/POST/DELETE; the reviewed local
  server accepts only POST/DELETE on `/mcp`. This corroborates a stale artifact,
  but neither this nor the remote ref proves its exact deployed Git SHA.
- Existing modifications preserved: `README.md`, `query.py`, `recommendations.py`,
  `search.py`; existing untracked evaluation/test files are listed in the companion
  [remediation report](REMEDIATION_REPORT.md). The index remains empty.
- No deploy manifest was found. The configured SpringWinter source ref/image and
  rejected upstream Host remain unverified.

**Exact latest committed release available:** `2dd37a2a63377074f3f909a9bff1f2e489def570`.
**Latest parsing candidate:** uncommitted working tree based on that SHA; it has no
commit hash yet. It cannot honestly be identified as a new immutable Git release.
Review/capture it separately before authorizing a rollout that includes those fixes.
No staging or commit was performed. Existing rollback server on port 8000 and
candidate on 8031 were preserved.

## Verification rerun for this investigation

| Check | Result |
|---|---|
| Full Windows unit suite | PASS, 48/48, 0.422 s |
| Full local proxy set | PASS, 37/37; startup 4.411 s, peak process 651.86 MiB in that run |
| Dependency consistency | PASS, `pip check` |
| Supplied smoke, isolated candidate port 8033 | PASS |
| Native advanced regressions, port 8033 | PASS, 20/20; includes four unsupported-request safety checks, not feature fulfillment |
| Exact public Host locally, no port and `:443` | PASS, MCP initialize HTTP 200 in both cases |
| Unlisted Host locally | PASS, HTTP 421; exact rejected hostname recorded in local log |
| Unapproved Origin locally | PASS, HTTP 403; Origin validation unchanged |
| Real MCP tool discovery and search using public Host locally | PASS, exact schemas/revision, catalog-grounded IDs, expected ordering and valid empty response |
| Public health | PASS, 200 and 105126 products |
| Public initialize and supplied public smoke | FAIL, 421; smoke exit 1 |
| Deployed revision, public server logs | BLOCKED, management access/configuration unavailable |

The local real search used `query="black dress"`, exact Black/Dress filters,
max_price 2000, price ascending, limit 3. Results: `0401044004` (Cora Dress),
`0458239022` (Tess), `0502522001` (Marc dress), each INR 999. The MCP output
contains only original string IDs as required; names/prices were looked up in
the supplied catalog for verification, not added to the tool response.

All eleven source hashes in `evaluation/reports/remediation-checks.json` match
current working files. Server, Dockerfile, dependency pins, supplied smoke client,
both published schemas and catalog have no diff against HEAD. Catalog SHA-256:
`05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073`.
Tool name `search_products`, protocol `2025-11-25`, validation errors, filtering,
sorting/null placement and pagination are covered by the rerun tests/smoke.

Commands run from the repository root:

```powershell
git branch --show-current
git rev-parse HEAD
git --no-optional-locks status --short --untracked-files=all
git diff -- README.md query.py recommendations.py search.py
git diff --cached --stat
git ls-remote --heads origin main
git diff --exit-code HEAD -- server.py Dockerfile requirements.txt schemas data/products.json smoke_test.py
git diff --check
Get-FileHash data/products.json -Algorithm SHA256
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe evaluation/run.py --split all --output .audit-tmp/public-fix-proxy.json
.\.venv\Scripts\python.exe -m pip check
```

The isolated server was launched with process-local `HOST=127.0.0.1`, `PORT=8033`,
`WEB_CONCURRENCY=1` and the exact allowlist above:

```powershell
Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList 'server.py' -WindowStyle Hidden -RedirectStandardOutput '.audit-tmp/public-host-local.stdout.log' -RedirectStandardError '.audit-tmp/public-host-local.stderr.log'
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8033/mcp
.\.venv\Scripts\python.exe evaluation/advanced.py http://127.0.0.1:8033/mcp --output .audit-tmp/public-fix-advanced.json
.\.venv\Scripts\python.exe .audit-tmp/verify_public_host.py
.\.venv\Scripts\python.exe smoke_test.py https://web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev/mcp
```

Scratch diagnostics are ignored and contain no required runtime changes. The first
Host verification helper incorrectly expected full product objects; it was corrected
to verify the published ID-only output via catalog lookup and then passed. This was
a diagnostic assertion error, not a server defect. Raw evidence is in
`.audit-tmp/public-host-verification.json`, `public-fix-proxy.json`,
`public-fix-advanced.json`, `public-fix-smoke.log` and local server logs. Prior
container measurements are recorded in the remediation report; no new image build
was needed for this environment-only fix.

## Rollout gate and next action

**Next action:** open/provide the actual SpringWinter web-service deployment settings
and logs page so the configured source revision and rejected Host can be verified.
Then explicitly authorize the specific allowlist/restart or reviewed release rollout.
The supplied benchmark dashboard is not that deployment page.

After authorized changes, require public health 200/count 105126, successful MCP
initialization, supplied smoke PASS, catalog-verified real search and no unexpected
Host rejection in public logs. Until then: **NO-GO for another benchmark attempt**.
No official score improvement is predicted by these local checks.
