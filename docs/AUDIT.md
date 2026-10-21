# Phase 1 audit — 21 October 2026

Completed before production code edits. Read AGENT.md, the full brief (including
scoring and schema appendices), both schema files, search.py, server.py, README,
requirements, Dockerfile, ignores, all existing tests and smoke_test.py.

## Contract and baseline

The supplied 106,498,333-byte catalog matches SHA-256
`05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073`.
There are 105,126 unique IDs, all strings. Do not rewrite the data. Git status with
LFS disabled reports the materialized JSON as modified relative to its pointer;
this is not evidence of changed catalog bytes. Normal Git status hits a sandbox
Git LFS shell permission failure.

Existing filtering uses inclusive bounds and AND, exact case-insensitive trimmed
string comparisons, and excludes null ratings from minimum-rating filters.
Sorting uses stable ascending-ID ties and null ratings last in both directions.
Whitespace query enumerates the exact filtered catalog; offset follows ordering.
Validation rejects extra fields, blank filters, bad ranges and nonfinite numbers.
The SDK advertises the schemas and returns structuredContent plus matching JSON
text; synchronous search runs on a worker thread. Recommendations are always
empty. Query tokens must ALL occur somewhere in name/description/attributes.

Measured against the unmodified local Docker image `polaris-search:audit`, Python
3.12 Linux, on this workstation (not the official runner):

| Check | Result |
|---|---|
| `python -m unittest discover -s tests -v` | 5/5 pass |
| official `smoke_test.py` against local container | pass |
| Docker build | pass, pinned requirements install |
| standalone GET /mcp with SSE Accept | FAIL: opens a stream; brief requires 405 |
| catalog load + baseline index | 5.334 s |
| peak process RSS after load | 740.8 MiB (`resource.ru_maxrss`) |
| 25 direct filter/field-sort calls | median 75.92 ms, nearest-rank p95 194.13 ms |

Five direct searches per query, warm process; these are diagnostic samples, not
an estimate of the official performance score:

| Query | Results/recommendations | Median ms |
|---|---:|---:|
| cotton top | 10/0 | 515.93 |
| black dress | 10/0 | 413.32 |
| dress under INR 2000 | 0/0 | 373.68 |
| black jeans and white T-shirts | 0/0 | 384.42 |
| dress with a matching bag | 0/0 | 325.73 |
| dres | 10/0 | 367.19 |
| something comfortable for a lazy Sunday | 0/0 | 310.75 |
| spaceship engine | 0/0 | 328.23 |
| black dress made of unobtainium | 0/0 | 363.87 |

Presence alone does not prove quality (notably `dres` occurs in source names).
No semantic relevance grades or official score were measured in this audit.
The additional GET probe ran after the first audit summary and revealed a protocol
gap not covered by the public smoke test. Fix this before retrieval work.

Initial host `python` was 3.15 without jsonschema. A workspace `.venv` uses 3.14
and the unchanged pins. Sandbox temp-path permissions initially broke ensurepip;
using a workspace scratch directory and pip's --python option resolved setup.
Package downloads and Docker engine access required execution outside the
sandbox. No cloud resources, publishing, deployment or official attempts occurred.

## MODA review

Inspected public revision `b6513ca77e076b090427ffe13f4959446a15662e`:
[license](https://github.com/hopit-ai/Moda/blob/b6513ca77e076b090427ffe13f4959446a15662e/LICENSE),
[dependencies](https://github.com/hopit-ai/Moda/blob/b6513ca77e076b090427ffe13f4959446a15662e/requirements.txt),
[configuration](https://github.com/hopit-ai/Moda/blob/b6513ca77e076b090427ffe13f4959446a15662e/configs/phase1.yaml),
[full pipeline](https://github.com/hopit-ai/Moda/blob/b6513ca77e076b090427ffe13f4959446a15662e/benchmark/eval_full_pipeline.py),
[hybrid retrieval](https://github.com/hopit-ai/Moda/blob/b6513ca77e076b090427ffe13f4959446a15662e/benchmark/eval_hybrid.py),
[SPLADE pipeline](https://github.com/hopit-ai/Moda/blob/b6513ca77e076b090427ffe13f4959446a15662e/benchmark/eval_splade_pipeline.py),
and [inference CLI](https://github.com/hopit-ai/Moda/blob/b6513ca77e076b090427ffe13f4959446a15662e/hf_repos/moda-fashionsiglip-multiview-203m/inference.py).

- MIT source license permits adaptation with copyright/license preservation.
  Verify any chosen checkpoint's separate license; dependencies and datasets have
  their own licenses. No MODA code is incorporated in the initial implementation.
- Config assumes H&M CSV article fields, OpenSearch BM25, cached FAISS indexes,
  and external query/qrel files. Full pipeline uses dtype=str (good for IDs),
  field weighting, GLiNER attribute boosts, rank fusion, then a cross-encoder.
  Its NER should-clauses do not enforce hard constraints. Its bounded top-k
  retrieval cannot implement exact filtered enumeration or deep field-sorted pages.
- Some dense caches check length rather than catalog identity. Polaris indexes
  must instead validate catalog hash, ordered original string IDs and build version.
  The CLI's image filenames are item IDs: an adapter would be essential.
- Useful concepts: field weighting, offline representations, rank fusion, ablation
  evaluation and separate reranking. Do not copy preset weights or thresholds.
- Large dependencies include torch/torchvision, open-clip, sentence-transformers,
  transformers, GLiNER, FAISS, numpy/pandas/pyarrow and OpenSearch client. The
  historical scripts also expect locally trained checkpoints not present here.
- [Model/architecture description](https://github.com/hopit-ai/Moda/blob/b6513ca77e076b090427ffe13f4959446a15662e/FSL_203M_SYSTEM_ARCHITECTURE.md):
  203M-parameter multimodal encoder, 768 dimensions, two query encodings, three
  stored gallery vectors/routes. For Polaris, three fp16 vectors alone would use
  about 462 MiB, excluding ANN, weights, images, catalog and runtime. This is a
  calculation, not measured deployment memory or latency.
- [Reproduction guide](https://github.com/hopit-ai/Moda/blob/b6513ca77e076b090427ffe13f4959446a15662e/REPRODUCE.md)
  describes a >=16 GB GPU and ~60 GB disk for its full external benchmark sweep;
  these are not minimum requirements for Polaris or a measured local cost.
- Its historical H&M experiment and academic image benchmarks differ in corpus,
  query provenance, labels, scoring and constraints from Polaris's live Bedrock
  grades. Reported gains do not transfer. No external products, labels, model
  downloads, training, image downloads or hosted inference are needed initially.

## Prioritized implementation plan

| Order | Change | Expected benefit | Cost / risk | Gate |
|---|---|---|---|---|
| 1 | Expand independent contract tests and freeze local train/held-out queries | protect 25-point validity area | low / low | exact oracle pages, schema, errors |
| 2 | Exact inverted postings; keep baseline ranking initially | lower lexical latency | low / low | identical outputs and timings |
| 3 | Parse prose constraints with explicit-filter precedence | recover ordinary shopping sentences | medium / medium | positive and conflict/negative regressions |
| 4 | Field weighting/phrase evidence and conservative aliases | improve lexical ranking and typos | medium / medium | local proxy grades and abstention |
| 5 | Split mixed choices; deterministic coverage ranking | cover requested items | medium / medium | shared limit and pagination |
| 6 | Separate complementary retrieval and filter scope | useful accessories | medium / medium | compatibility, scoped budgets, page references |
| 7 | Calibrate abstention, measure startup/RSS/concurrency | avoid irrelevant results | medium / medium | held-out checks, smoke/container |
| 8 | Optional offline semantic retrieval + fusion | uncertain | high / high | meaningful measured held-out gain first |

Keep the architecture in-process and dependency-light. Preserve published schemas,
tool name, protocol revision, SDK transport and exact catalog filter/sort path.
Freeze local expectations before tuning, and identify proxy relevance metrics as
proxies rather than claiming hidden benchmark scores. Every behavioral increment
needs targeted regression tests and recorded before/after results.
