# Final matching-boundary release candidate

22 October 2026. Parent production release:
`16e55eadc2b302514fb03c874efa4436c1977a96`.

**Local verification: PASS. Public rollout/verification: pending. No official
benchmark attempt is authorized or used.** Earlier review reports describe earlier
trees; the independent blockers recorded there were fixed and retested here.
This does not predict an official score or certify arbitrary natural language.

## Targeted fix

`QueryParser.suffix_complement` now collects eligible boundaries and prefers an
explicit item-bearing `with` attachment over preceding mixed-choice connectors.
An indefinite article followed only by a color no longer counts as a product head.
This preserves both primary choices in `dress plus skirt with a bag to match` and
keeps a coordinated print attribute, with its price ceiling, on the primary dress.

Coordinated color modifiers on known garment attribute heads are retained as
mandatory normalized source phrases before color-facet extraction. A black-only
floral print cannot satisfy `black and white print`. Existing source phrase
retrieval enforces that evidence; no ranking rewrite or dependency was added.
This conservative literal policy can miss paraphrases and punctuation variants.

Only `query.py` changed further at runtime relative to the last reviewed candidate.
The retained `search.py` source-phrase constraint and recommendation coverage work
remain part of the complete candidate. No security, protocol, dependency, catalog
or schema changes were made.

## Evidence and limits

- The unchanged independent review script passes all three methods/four mixed
  subtests on Windows. Its original bytes and old patches are preserved under
  `.audit-tmp/final-boundary-fix-input/` (nineteen input files with byte hashes).
- `tests/test_final_boundary_review.py` retains those original assertions and adds
  complete color-phrase positive/negative controls, parsed category budgets and
  recommendation-reference checks. No existing expectation was weakened.
- Windows and freshly built Linux full unit/security suites: **104/104 each**.
- Original proxies **37/37**, existing quality **39/39**, frozen cases **18/18**,
  existing scope cases **11/11**; development and held-out partitions included.
- Native Windows quality **39/39**, advanced **20/20**, frozen **18/18**, scope
  **11/11**; supplied Windows and Linux MCP smoke checks pass.
- Six new critical full-catalog cases pass on both Windows and Linux MCP, with
  identical structured responses. Their plans, IDs, filters and references were
  checked, not only response counts.
- Windows and Linux dependency checks and the local Docker build pass.

`evaluation/final_boundary_cases.json` contains the exact critical requests plus
nonempty budget/attribute controls. The plain `plus`/`and` mixed queries return
five dresses and five skirts. Their unbudgeted prices are intentionally unrestricted.

An independent source scan found **zero Dress records with the literal normalized
phrase `black and white print`**. Both print requests therefore return empty arrays
under this policy, including the one capped at 1000. This is conservative rejection,
not proof that the catalog has no semantically equivalent prints. Source-positive
fixtures ensure the parser can retrieve an actual matching record when present.

Nonempty full-catalog checks avoid vacuous budget claims:

- `dress under 1000 plus skirt under 1300 with a bag under 500 to match` returns
  ten eligible primary records covering both types; all dress prices are 999 and
  every skirt is at most 1300. All five recommended bags cost 499.
- `dress with a shirt collar under 2500 and a bag under 500 to match` returns
  primary `0743126001`, price 2299, with exact collar evidence. Five bags at 499
  each reference that primary ID. Leading zeros are preserved.

Critical six-case local p95 samples were 162.38 ms Windows and 172.69 ms Linux.
These small sequential samples are not official performance estimates. Comfort,
styling and semantic ranking remain ungraded locally; owned-item and combined
basket planning remain unsupported. Passing tests cannot guarantee future 25/25
validity or 91+ overall. Use no official attempt on this evidence alone.

## Release contents and preservation

The reviewed complete candidate has eighteen files: the fifteen listed in
`.audit-tmp/FINAL_MATCHING_PARSER_REVIEW.md`, plus:

- `tests/test_final_boundary_review.py`
- `evaluation/final_boundary_cases.json`
- `docs/FINAL_BOUNDARY_RELEASE.md`

The latest task changes only `query.py` and adds those three files. Historical
documents/reports and the original review/proposal patches are not overwritten.
Ignored audit inputs, native logs, profiling files and generated build artifacts
are excluded. The catalog, server, Dockerfile, pins, schemas and supplied smoke
client remain identical to the production parent. A targeted secret scan is part
of the release gate; no credentials are needed in this commit or container.

The final SHA is recorded after creating the authorized local commit. Before
committing, export the index, verify its blobs against tested contents, materialize
the official LFS object and rerun the unit/critical/proxy checks there. The GitHub
remote is `BUGHUNTER-SACHIN/Polaris-Hackathon-Base-MCP`, branch `main`; its last
verified remote tip was the unchanged production parent. No push is part of this
local release preparation.

## Commands and publication gate

From the repository root with the Windows venv:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe .audit-tmp/final_release_review_adversarial.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe evaluation/run.py --split all --output .audit-tmp/final-boundary-proxies.json
.\.venv\Scripts\python.exe evaluation/quality.py --split all --output .audit-tmp/final-boundary-quality.json
.\.venv\Scripts\python.exe evaluation/run47.py --split all --output .audit-tmp/final-boundary-frozen.json
.\.venv\Scripts\python.exe evaluation/run47.py --cases evaluation/matching_revision_cases.json --split all --output .audit-tmp/final-boundary-scope.json
.\.venv\Scripts\python.exe evaluation/run47.py --url http://127.0.0.1:8054/mcp --cases evaluation/final_boundary_cases.json --split all --output .audit-tmp/final-boundary-six-critical-native.json
.\.venv\Scripts\python.exe evaluation/run47.py --url http://127.0.0.1:8055/mcp --cases evaluation/final_boundary_cases.json --split all --output .audit-tmp/final-boundary-six-critical-linux-native.json
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8054/mcp
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8055/mcp
docker build -t polaris-search:final-boundary-release .
docker run --rm --network none polaris-search:final-boundary-release python -m unittest discover -s tests
docker run --rm --network none polaris-search:final-boundary-release python -m pip check
```

Native 39/20/18/11 suites additionally used `quality_mcp.py`, `advanced.py` and
`run47.py` against isolated Windows port 8054. Raw outputs remain in ignored
`.audit-tmp/final-boundary-*.json` and logs. Original production-like port 8037
was not replaced; the new Linux test container is isolated on loopback port 8055.

### Required SpringWinter rollout, after explicit authorization

No authenticated hosting deployment connector or management URL is available in
this session. The user's earlier repository/main confirmation is recorded, but
the exact current UI controls and active image revision cannot be independently
verified here. Do not use the benchmark run page as deployment metadata, and do
not invent a SpringWinter CLI command or assume an image-push log proves rollout.

1. Record the active service revision/image digest as rollback. Confirm the hosting
   GitHub connection points to this fork and `main`, and whether a push auto-deploys.
2. With publication/rollout authorization, fast-forward only:
   `git push origin main:main`. Verify `git ls-remote --heads origin main` equals
   the exact new local release SHA. Never push upstream or force-push.
3. On the existing **web-service hosting deployment/build page** where GitHub was
   connected, use its supported build/redeploy action for that new SHA. If the
   service has a commit/ref pin, update it to the release SHA using the documented
   control; otherwise ensure the branch build actually resolves the new `main`.
   A rebuild of an old cached image is insufficient. Exact control labels require
   that authenticated page; they are not asserted here.
4. Build from repository-root Dockerfile/context with the real LFS catalog, retain
   the existing working port/probe configuration and one-worker startup
   `python server.py`. Keep Host/Origin settings unchanged. Health is `/healthz`,
   MCP is `/mcp`; do not replace the platform's verified port with a guessed one.
5. Require a build record showing the resolved new commit and published image
   digest, then an active deployment record showing that image running and ready.
   Published and running images are separate facts. Stop if the source resolves
   to the starter or old production SHA.
6. Verify public health 200/count 105126, supplied public smoke, and all six critical
   native queries against this local release. Confirm exact response parity and
   no legitimate Host rejections in runtime logs. Only then reconsider benchmark
   readiness; an official attempt still requires separate authorization.

Read-only public commands after the rollout (not executed as proof of this release
before it is published):

```powershell
curl.exe --fail-with-body https://web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev/healthz
.\.venv\Scripts\python.exe smoke_test.py https://web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev/mcp
.\.venv\Scripts\python.exe evaluation/run47.py --url https://web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev/mcp --cases evaluation/final_boundary_cases.json --split all --output .audit-tmp/final-boundary-public-critical.json
```

**Current decision: GO for a local reviewed release commit; NO-GO for spending the
last attempt until the exact release is deployed and public checks pass.**
