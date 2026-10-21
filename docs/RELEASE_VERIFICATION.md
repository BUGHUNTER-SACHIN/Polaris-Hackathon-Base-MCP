# Reviewed quality release — 21 October 2026

The user explicitly authorized committing/pushing this reviewed candidate and
redeploying after the source was confirmed. The user then confirmed in SpringWinter
settings: repository `BUGHUNTER-SACHIN/Polaris-Hackathon-Base-MCP`, branch `main`.
That confirmation establishes the publication target; it does not establish the
previously deployed SHA, the platform's auto-deploy behavior or a completed rollout.

This document records pre-publication verification. Commit/push/rollout outcomes,
the actual release SHA and public checks must be recorded from command/platform
outputs in the final report. Do not infer them from this document's existence.

## Candidate and test correction

Base: `2dd37a2a63377074f3f909a9bff1f2e489def570`, following runtime release
`689e11b7e26d996e8615edaf0c854ebb8c244176`. Before publication, live remote `main`
was `e1cbc5fe8d4831719c530309075cccea2a278401`. No shared history is rewritten.
The current changes capture the preserved remediation/quality work documented in
`QUALITY_RELEASE_PLAN.md`. No additional ranking rewrite or application feature was
introduced while finalizing this release.

The remaining 38/39 check was investigated against the full frozen catalog. Its
literal grading rule accepts only Skirts whose name/description contains `floral`;
exactly one product meets that rule. Requiring ten such products was an invalid
local test expectation. The case now explicitly requires the one available primary,
and independently verifies `reference_count=1` against the catalog. All other
cases retain their original minimum counts and constraints. The server still returns
one primary and five catalog-grounded complementary bags for that request.

The original 39-case file is preserved byte-for-byte as
`evaluation/reports/quality-cases-v1.json`, SHA-256
`4489cfd3e012f89c0bb266e087b301deb4bfc5bdd56de827a9268f1654cdc39b`.
Original 38/39 reports remain unchanged. Corrected case-file SHA-256:
`f4a1b44338ec62939eb70493b7a4ab394c4849963526fb8e37fe06044b955f3e`.
**The corrected 39/39 is a test correction, not a search-quality improvement or
a comparable increase in semantic score.** Conceptual floral/flower recall remains
unmeasured beyond the literal rule. Nothing is fabricated to fill missing slots.

One regression method checks this small-pool behavior and rejects an incorrect
reference count. Both quality evaluators now exit nonzero if a case fails; they
previously printed failures but exited successfully. Public MCP output/schema and
application runtime code were not changed by these finalization fixes.

## Checks actually completed before staging

| Check | Result |
|---|---|
| Windows full unit/security suite | 60/60, 1.345 s |
| Linux/Python 3.12 full unit/security suite | 60/60, 0.973 s |
| Dependency consistency | Host and Linux container PASS |
| Existing full-catalog local proxies | 37/37 |
| Corrected broader direct quality set | 39/39 |
| Supplied local MCP smoke | PASS |
| Advanced native MCP checks | 20/20; four unsupported-request safety checks, not native outfit-planning success |
| Corrected broader native MCP checks | 39/39 |
| Original held-out/full-slot evidence | Retained 13/14 and 38/39, not rewritten |

The staged tree is to be exported to a new isolated directory, the LFS catalog
materialized and checksum-verified, and tests/container smoke repeated on that
snapshot before commit. Checks on the working tree alone do not prove staged
snapshot identity. The final response must distinguish actually completed gates
from planned deployment gates.

The public protocol smoke previously passed, but four natural-language requests
returned zero results there while the local release/candidate returned ten each
(plus five recommendations for the complementary request). Deployment success
must include those comparisons and broader native cases, not only health/smoke.

## Release scope and invariants

The reviewed release allowlist is the 23 files in `QUALITY_RELEASE_PLAN.md`, plus:

```text
docs/RELEASE_VERIFICATION.md
evaluation/reports/quality-cases-v1.json
evaluation/reports/release-verification.json
```

Total: **26 changed/new files**. The index must contain exactly this list, with no
`.audit-tmp/`, credentials or unrelated files. The supplied schemas, tool name
`search_products`, protocol `2025-11-25`, dependency pins, Dockerfile, server and
catalog remain unchanged against base HEAD. Catalog SHA-256:
`05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073`.

The application's original string IDs, leading zeros, inclusive hard filters,
explicit precedence, sort/null/tie/page/validation behavior and recommendation
references remain covered by tests. Host/Origin checks stay enabled; retain the
service's functioning exact `MCP_ALLOWED_HOSTS` setting during redeployment.

## Commands and rollout gates

From the repository root in PowerShell:

```powershell
git --no-optional-locks status --short --untracked-files=all
git rev-parse HEAD
git branch -avv
git remote -v
git ls-remote --heads origin main
git diff -- README.md query.py recommendations.py search.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe evaluation/run.py --split all --output .audit-tmp/publish-original-proxies.json
.\.venv\Scripts\python.exe evaluation/quality.py --split all --output .audit-tmp/publish-quality-direct.json
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8035/mcp
.\.venv\Scripts\python.exe evaluation/advanced.py http://127.0.0.1:8035/mcp --output .audit-tmp/publish-advanced.json
.\.venv\Scripts\python.exe evaluation/quality_mcp.py http://127.0.0.1:8035/mcp --output .audit-tmp/publish-quality-native.json
docker build -t polaris-search:publish-review .
docker run --rm --network none polaris-search:publish-review python -m unittest discover -s tests -v
docker run --rm --network none polaris-search:publish-review python -m pip check
```

After exact allowlist staging/review and isolated snapshot gates, authorized
publication commands are:

```powershell
git diff --cached --check
git diff --cached --name-only
git diff --cached
git commit -m "fix: release grounded Polaris query and recommendation improvements"
git rev-parse HEAD
git push origin main:main
git ls-remote --heads origin main
```

Do not push upstream or force-push. A successful push establishes publication to
the confirmed GitHub branch, not successful SpringWinter deployment. Observe the
platform build/rollout and expose no secrets. If automatic deployment cannot be
verified, the user must open the hosting page for this web service, select the new
commit on the confirmed repo/main, and trigger its supported redeploy workflow.
Preserve Host/Origin settings and materialize the official LFS catalog.

After rollout, execute:

```powershell
.\.venv\Scripts\python.exe smoke_test.py https://web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev/mcp
.\.venv\Scripts\python.exe evaluation/quality_mcp.py https://web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev/mcp --output .audit-tmp/published-public-quality.json
```

Also run the four original exact queries against both the pinned local snapshot and
public endpoint, verify catalog IDs/constraints/ordering/references/empty responses,
and measure completed-call latency. Record actual deployed SHA/image if exposed;
otherwise state that it is unavailable even if functional parity passes. Server logs
are required to confirm no unexpected Host rejections; absence of HTTP 421 in probes
alone is not a complete log audit.

No official attempt is authorized. Protocol/constraint/proxy correctness does not
establish 91+, semantic suitability or official performance eligibility. Native
owned-item outfit context and basket planning remain unsupported. Another official
attempt is premature until the intended code is publicly verified; even then it
requires separate authorization and a candid review of the semantic quality gaps.
