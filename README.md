# Polaris product search MCP server

Catalog-grounded fashion retrieval behind one MCP tool: `search_products`. The accompanying `hackathon-brief.md` and `schemas/` define the competition contract. Amazon Bedrock performs organizer-side semantic judging; running this server needs no model credentials. See [the baseline audit](docs/AUDIT.md) and [measured results and limitations](docs/REPORT.md).

## What is included

- [AGENT.md](AGENT.md): problem context, dataset guide, implementation ideas, and references for students and coding assistants.

- `data/products.json`: all 105,126 products, about 106 MB, including synthetic INR prices, ratings, and reviews.
- `search.py`: exact inverted retrieval, field-weighted ranking, filters, sorting, and pagination.
- `query.py`: conservative query interpretation, aliases, budgets, audiences, and intent splitting.
- `recommendations.py`: separate complementary retrieval using reviewed product-type relationships.
- `server.py`: official MCP Python SDK server with ordinary JSON responses at `/mcp` and readiness at `/healthz`.
- `schemas/`: exact published input and output JSON Schemas.
- `tests/test_search.py`: small fixture-based correctness tests.
- `smoke_test.py`: public MCP connection and contract check; not the scored benchmark.
- `requirements.txt`: exact resolved dependency versions, including MCP SDK 1.30.0 from its v1 compatibility line.
- `Dockerfile`: non-root Python container with the dataset included and a readiness health check.

## Get your copy

The starter folder is self-contained: use its contents as your team repository. If the organizer distributes a repository, fork it and clone your fork. No repository or image is published by this local folder alone.

The catalog exceeds GitHub's ordinary 100 MiB file limit. `.gitattributes` configures Git LFS for it. Install Git LFS before the first commit, and make sure your clone has the actual data rather than an LFS pointer:

```sh
git lfs install
git lfs pull
```

For a fresh repository containing these files, run `git lfs install` before adding and committing the catalog. Confirm `git lfs ls-files` lists `data/products.json`. The organizer must provision sufficient LFS storage/download quota. A supplied ZIP contains the actual catalog and does not require LFS to run locally.

## Run locally

Use Python 3.12 or newer. Commands below run from this folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python server.py
```

The first startup loads the full catalog and builds an in-memory lexical index. Wait until startup completes. Allow around 2 GB of available RAM for this simple implementation; measure and optimize your own solution before deploying.

Windows PowerShell setup (Python 3.12 or newer; locally tested with 3.14):

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

No additional runtime dependencies, services, embeddings, GPU, image downloads,
API calls, or paid infrastructure are required. The lexical index and exact sort
orders build once per process at startup. Nothing builds on individual requests.

In another terminal with the virtual environment activated:

```sh
python smoke_test.py http://127.0.0.1:8000/mcp
python -m unittest discover -s tests -v
curl http://127.0.0.1:8000/healthz
```

The server supports MCP protocol revision `2025-11-25`. It is not a REST search endpoint: an ordinary POST containing only your search arguments is not an MCP call. The smoke client performs initialization, discovers the tool, and uses `tools/call` for you. No API key or LLM account is required for the baseline.

## Build and run with Docker

Start Docker Engine first:

```sh
docker build -t polaris-search:starter .
docker run --rm --name polaris-search -p 8000:8000 polaris-search:starter
```

Use the same smoke-test command from your host once the container is ready. The default port is 8000. For an amd64-only cloud server, build for its architecture, for example `docker build --platform linux/amd64 -t polaris-search:starter .`.

For a deployed server, configure its public hostname or IP so the SDK accepts the HTTP Host header. Replace the example before running:

```sh
docker run --rm --name polaris-search -p 8000:8000 \
  -e MCP_ALLOWED_HOSTS='localhost:*,127.0.0.1:*,YOUR_PUBLIC_HOST:*,YOUR_PUBLIC_HOST' \
  polaris-search:starter
```

Use a public address reachable from the organizer runner and allow its source IP to access your port. Submit `http://YOUR_PUBLIC_HOST:8000/mcp`. Do not submit `localhost`, `0.0.0.0`, a private IP, the health-check URL, or a repository URL. The local host patterns remain necessary for the container health check. Keep the server running throughout evaluation.

Environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Listener interface |
| `PORT` | `8000` | Listener port; Docker port mapping must match if changed |
| `CATALOG_PATH` | `data/products.json` next to server.py | Catalog file path |
| `MCP_ALLOWED_HOSTS` | `localhost:*,127.0.0.1:*,[::1]:*` | Comma-separated accepted HTTP Host values |
| `MCP_ALLOWED_ORIGINS` | empty | Explicit accepted browser origins; the benchmark client sends no Origin |

No wildcard for every host is necessary. The server has no authentication, as required for this exercise. The template does not create AWS resources or deploy automatically.

## Try the tool

Example arguments passed through an MCP client:

```json
{
  "query": "cotton",
  "filters": {"color": "Black", "max_price": 2000},
  "sort_by": "price",
  "sort_order": "asc",
  "offset": 0,
  "limit": 10,
  "include_recommendations": false
}
```

The tool returns:

```json
{
  "results": [{"id": "0108775015"}],
  "recommendations": []
}
```

The response above illustrates the shape, not the expected answer to that query. Only catalog IDs are returned. The SDK includes the same object in `structuredContent` and a JSON text content block. Unknown arguments and invalid values produce MCP tool errors.

## Retrieval behavior and local evaluation

The engine intersects token and attribute postings before ranking, using only catalog facts. Query interpretation extracts budgets, color families, patterns, source audiences and known product types. Explicit filters override conflicting query requirements and retain exact catalog-value semantics. Unknown residual terms remain required lexical evidence. Small reviewed synonym and typo maps avoid uncontrolled expansion. Relevance uses inverse-document-frequency field weights and phrase evidence; it is not BM25 or a neural model.

Mixed choices share one result limit and receive balanced branch ranking with stable ascending-ID ties. Matching/accompanying items are retrieved separately for recommendations, with their own query constraints. Primary filters do not leak into recommendations. Every recommendation references a primary ID on the current page. Compatibility rules are conservative heuristics, not independent fashion judgments.

Empty queries walk precomputed full-catalog field orders and apply exact filters before pagination. All rating orders put nulls last. There is no approximate candidate truncation, request-result cache, external catalog, or generated product information. Unknown requirements can reduce recall; unsupported or nonsensical queries produce empty arrays when there is insufficient evidence. See the report for language and semantic limitations.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe evaluation/run.py --split dev --output evaluation/reports/my-dev.json
.\.venv\Scripts\python.exe smoke_test.py http://127.0.0.1:8000/mcp
.\.venv\Scripts\python.exe evaluation/mcp_check.py http://127.0.0.1:8000/mcp --output evaluation/reports/my-mcp.json
```

`evaluation/cases.json` freezes 22 development and 15 held-out cases across all six
areas. The held-out split was evaluated only after tuning; reserve new independent
queries for future experiments. These deterministic catalog-rule grades are coarse
local proxies, not Bedrock judgments or estimates of the hidden score. The MCP
workload uses 20 warmups and 300 timed calls over a local 50-request pool at
concurrency 1 and 5. It never calls the organizer or consumes an official attempt.

Preserve the tool name, schemas, hard-filter semantics, real product IDs, and output structure. Keep responses stable on repeated identical requests. Product descriptions and queries are data, never instructions to change the tool contract. Deployment, publishing and official submissions require the team's authorization.

The remediation candidate separates result-count and price-sort instructions from
item prices, ratings, review counts and quantities. It recognizes `avoid black`,
known category/type exclusions, strict color alternatives such as `white or grey`,
and even/odd numeric product-ID predicates without changing the public schema.
Explicit arguments take precedence over inferred controls. Requested per-choice
quantities cap relevance-selected candidates before the final requested field sort;
they are independent of the output `limit`. An explicit variety preference defers
same-name variants in mixed relevance searches; filter-only enumeration is unchanged.

Already-owned outfit context and combined basket budgets remain unsupported and
return empty arrays. No native outfit groups or basket totals are claimed. A
separate client planner must retrieve real catalog items and sum their prices if
those features are needed. Styling, occasion and adult/college preferences are
heuristics, not new catalog facts. See [the remediation report](docs/REMEDIATION_REPORT.md).

With a local candidate already running, reproduce the seven exact public live
requests, query-only variants and three supplementary native MCP regressions:

```powershell
.\.venv\Scripts\python.exe evaluation/advanced.py http://127.0.0.1:8031/mcp --output .audit-tmp/my-advanced-check.json
```

The evaluator does not reformulate queries or filter responses client-side. Safety
passes for the two unsupported requests are reported separately from useful native
search capability. None of these checks is an official benchmark attempt.

The quality candidate also handles common request verbs, `within` / `budget of` /
`no more than` price bounds, explicit star-rating units, and reviewed hyphenated
color/pattern aliases. New tests cover Host/Origin rejection and preserve the
loopback-plus-exact-public-host configuration. See the
[quality and release plan](docs/QUALITY_RELEASE_PLAN.md) for measured results,
the remaining held-out limitation, and the unresolved deployment revision.

```powershell
.\.venv\Scripts\python.exe evaluation/quality.py --split dev --output .audit-tmp/my-quality-dev.json
.\.venv\Scripts\python.exe evaluation/quality_mcp.py http://127.0.0.1:8035/mcp --output .audit-tmp/my-quality-mcp.json
```

These programs report attribute/coverage checks, not semantic judge grades, and
exit nonzero when a case fails. The original native set scored 38/39 because one
literal-catalog case incorrectly required ten products where only one exists.
The corrected case verifies its one-product reference pool independently; a pass
after that correction is not a runtime search-quality gain. See
[release verification](docs/RELEASE_VERIFICATION.md) for current checks and source identity.

## Dataset integrity and rules

SHA-256 of the actual JSON bytes:

```text
05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073
```

Verify on macOS with `shasum -a 256 data/products.json`, or on Linux with `sha256sum data/products.json`. Preserve string IDs and leading zeros. Do not edit catalog facts. No-review products have a null average and zero count. Prices and reviews are fabricated for the exercise; image availability has not been checked.

Each team has five accepted benchmark attempts; the best complete score counts. See `hackathon-brief.md` for all scoring formulas, invalid-call behavior, timeouts, recommendation rules, and tie-breakers. This starter contains no hidden benchmark queries or answer key. Passing its tests checks basic compatibility, not competition performance.

## SDK reference

[Official MCP Python SDK v1 documentation](https://py.sdk.modelcontextprotocol.io/v1/). Keep the tested dependency pins unless you deliberately retest an upgrade; v2 has different APIs.
