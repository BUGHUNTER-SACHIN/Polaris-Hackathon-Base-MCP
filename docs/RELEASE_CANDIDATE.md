# Reviewed release candidate — 21 October 2026

This candidate captures the tested lexical implementation from base commit
`e1cbc5fe8d4831719c530309075cccea2a278401`. It is prepared for review and staging,
not deployment or automatic commit. Earlier audit/readiness reports describe the
pre-release HEAD and remain historical evidence; staging does not itself change HEAD.

## Scope relative to HEAD

- Replace catalog-wide AND scanning with token/facet postings and precomputed exact
  field orders. Add weighted lexical/phrase ranking and deterministic mixed-choice
  coverage while retaining original catalog IDs and exact filtering/pagination.
- Add conservative query interpretation and separate complementary retrieval, with
  accessory budgets, audience scope, unique IDs and current-page references.
- Return HTTP 405 for standalone MCP GET; keep the SDK, public tool name, schemas,
  structured/text JSON responses and protocol revision unchanged.
- Preserve the supplied dependency pins and Docker entry point. Add regression and
  local evaluation coverage, deployment findings and Windows setup instructions.
- No model/API service, paid infrastructure, external product records or new runtime
  dependency is introduced. No existing source or evaluation evidence is rewritten
  as part of preparing this snapshot.

## Explicit staging list

The following **36 changed/new files** are the proposed release change set. Files
are added individually by this allowlist; no blanket `git add .` is used.

```text
.dockerignore
.gitignore
README.md
search.py
server.py
query.py
recommendations.py
tests/test_search.py
tests/test_contract.py
tests/test_index.py
tests/test_query.py
tests/test_ranking.py
tests/test_recommendations.py
tests/test_server.py
evaluation/cases.json
evaluation/run.py
evaluation/mcp_check.py
evaluation/reports/baseline-dev.json
evaluation/reports/baseline-heldout.json
evaluation/reports/final-all.json
evaluation/reports/final-dev.json
evaluation/reports/final-heldout.json
evaluation/reports/final-sources.json
evaluation/reports/index-dev-windows.json
evaluation/reports/index-dev.json
evaluation/reports/mcp-baseline.json
evaluation/reports/mcp-final.json
evaluation/reports/optimized-dev.json
evaluation/reports/parser-dev.json
evaluation/reports/ranking-mixed-dev.json
evaluation/reports/recommendations-dev.json
evaluation/reports/refined-dev.json
docs/AUDIT.md
docs/REPORT.md
docs/DEPLOYMENT_READINESS.md
docs/RELEASE_CANDIDATE.md
```

These **nine unchanged files** are already in HEAD/index and are inherited by the
candidate; they need no restaging:

```text
.gitattributes
AGENT.md
Dockerfile
data/products.json
hackathon-brief.md
requirements.txt
schemas/input.schema.json
schemas/output.schema.json
smoke_test.py
```

The resulting snapshot contains **45 files**, including the catalog's existing Git
LFS pointer. The official materialized catalog is 106,498,333 bytes, 105,126 products,
with SHA-256:

```text
05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073
```

Schemas, the LFS pointer, dependency pins and Dockerfile must match HEAD exactly.
Do not stage the materialized catalog as a replacement Git blob. Fresh checkouts
must fetch or otherwise verify/materialize that same LFS object before running.

## Inclusion and exclusion review

The 15 generated `evaluation/reports/*.json` files are deliberately retained as
small historical experiment evidence: baseline failures, intermediate changes,
final checks, latency samples and source checksums. They are not temporary profiling
logs or organizer answers. Their product references were checked against the frozen
catalog. Keeping them preserves the measurements and links in the audit/report;
do not overwrite them when rerunning validation.

All `.audit-tmp/` content stays ignored and outside the snapshot: downloaded MODA
source/configuration/license files, Black cache bytes, diagnostic helpers, build and
server logs, readiness profiles/results and release-check/export files. None is
imported by the application or needed by the documented portable unit/smoke/local
evaluation commands. The earlier readiness report embeds its material findings;
its extra scratch-only diagnostics are explicitly not a portable test suite.
No downloaded MODA implementation is incorporated in the release.

The reviewed release inventory has no matches for checked private-key, AWS/OpenAI/
GitHub token, bearer credential, credential URL/assignment or absolute user-home
path patterns. This is a scoped review, not proof against every possible secret
format. The excluded formatter cache contains local machine paths. Loopback example
URLs and portable `/app` container paths are intentional, not deployed endpoints.
No `.venv`, bytecode, cache, secret/config credential file, image export, temporary
profiling result or unrelated file belongs in the allowlist.

## Validation of the staged implementation

After staging, export the **Git index**, not the live working tree, into a fresh
ignored directory. Materialize the unchanged catalog pointer only from bytes whose
SHA-256 and size match that pointer; no other unstaged file may supply application
code. Verify each exported file against its staged Git blob after normal Git clean
filters. Build the Docker image using this export alone as its build context.

Rerun these documented checks against the export/image, storing new logs/results
outside the staged export or in disposable container storage:

```text
python -m unittest discover -s tests -v
python -m pip check
docker build -t polaris-search:release-candidate <index-export-directory>
docker run --rm polaris-search:release-candidate python -m unittest discover -s tests -v
docker run --rm polaris-search:release-candidate python -m pip check
python smoke_test.py http://127.0.0.1:<local-only-port>/mcp
python evaluation/run.py --split all --output <outside-snapshot-output>
python evaluation/mcp_check.py http://127.0.0.1:<local-only-port>/mcp --output <outside-snapshot-output>
```

Also verify the image's catalog digest/count, original string IDs, non-root process,
GET 405 and health response. Record the staged tree ID before and after testing;
the index and exported staged contents must still match. The final review message
associates actual test outcomes with that exact staged tree, rather than inserting
self-referential test results into this file after the tree has been tested.

## Remaining deployment limitations

Confirm the actual SpringWinter/hosting port, probe, Host/Origin, resource, shutdown
and organizer ingress requirements before deployment. Use the existing single-worker
entry point; an injected `WEB_CONCURRENCY=2` fails startup. The mutable Docker base
tag and package availability are remaining build-reproducibility limits; this task
preserves the previously tested configuration instead of silently upgrading it.
Historical local evaluation grades are coarse proxies; no official benchmark or
Bedrock score is claimed. Previously held-out queries are already consumed.

## Proposed commit message

```text
feat: add catalog-grounded Polaris search release candidate

- Add indexed lexical retrieval, query constraints and mixed-choice ranking
- Add scoped complementary recommendations and MCP GET compliance
- Preserve catalog, schemas and dependency pins; include tests and audit evidence
```

Stop before committing. Do not amend, push, deploy or run an official attempt as
part of this preparation.
