"""Local transport and exact-page workload; not an official benchmark attempt."""

import argparse
import asyncio
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.run import oracle
from search import INPUT_SCHEMA, OUTPUT_SCHEMA
from jsonschema import Draft202012Validator, ValidationError
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import McpError
import httpx


def workload():
    calls = []
    for i in range(50):
        args = {
            'limit': 10,
            'offset': 0,
            'sort_by': ('relevance', 'id', 'price', 'rating', 'review_count')[i % 5],
            'sort_order': 'asc' if i % 2 else 'desc',
        }
        filters = (
            {},
            {'color': 'Black'},
            {'product_type': 'Dress'},
            {'min_price': 500, 'max_price': 2000},
            {'min_rating': 4.0},
            {'audience': 'Menswear', 'color': 'White'},
            {'pattern': 'Stripe'},
            {'min_review_count': 3},
            {'color': 'NoSuchColor'},
            {'category': 'Shoes', 'max_price': 1500},
        )[i // 5]
        args['filters'] = filters
        calls.append(args)
    return calls


async def run(url, output, allow_get_stream=False):
    products = json.loads((ROOT / 'data/products.json').read_text(encoding='utf-8'))
    pool = workload()
    expected = [oracle(products, args) for args in pool]
    del products
    validator = Draft202012Validator(OUTPUT_SCHEMA)
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'GET', url, headers={'Accept': 'text/event-stream'}, timeout=5
        ) as response:
            get_status = response.status_code
        if not allow_get_stream:
            assert get_status == 405, f'standalone GET: {get_status}'
    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            assert init.protocolVersion == '2025-11-25'
            tools = (await session.list_tools()).tools
            assert len(tools) == 1 and tools[0].name == 'search_products'
            assert (
                tools[0].inputSchema == INPUT_SCHEMA
                and tools[0].outputSchema == OUTPUT_SCHEMA
            )

            async def call(index):
                started = time.perf_counter()
                error = None
                try:
                    result = await asyncio.wait_for(
                        session.call_tool('search_products', pool[index]), 10
                    )
                    assert not result.isError
                    payload = result.structuredContent
                    validator.validate(payload)
                    assert json.loads(result.content[0].text) == payload
                    assert [p['id'] for p in payload['results']] == expected[index]
                    assert payload['recommendations'] == []
                except (
                    AssertionError,
                    ValueError,
                    TimeoutError,
                    ValidationError,
                    McpError,
                    httpx.HTTPError,
                ) as exc:
                    error = type(exc).__name__ + ': ' + str(exc)
                elapsed = (
                    (time.perf_counter() - started) * 1000 if error is None else 10000
                )
                return {'pool_index': index, 'ms': elapsed, 'error': error}

            warmup = [await call(i) for i in range(20)]
            assert not any(x['error'] for x in warmup), warmup
            rows, workloads = [], []
            for repetition in range(3):
                for concurrency in (1, 5):
                    semaphore = asyncio.Semaphore(concurrency)

                    async def bounded(index):
                        async with semaphore:
                            return await call(index)

                    started = time.perf_counter()
                    batch = await asyncio.gather(*(bounded(i) for i in range(50)))
                    duration = time.perf_counter() - started
                    workloads.append(
                        {
                            'repetition': repetition,
                            'concurrency': concurrency,
                            'seconds': duration,
                            'correct_rps': sum(r['error'] is None for r in batch)
                            / duration,
                        }
                    )
                    rows.extend(
                        {**r, 'repetition': repetition, 'concurrency': concurrency}
                        for r in batch
                    )
    times = sorted(r['ms'] for r in rows)
    report = {
        'note': 'Local exact-page transport workload, not the organizer pool or a predicted score.',
        'url': url,
        'protocol': init.protocolVersion,
        'pool_sha256': hashlib.sha256(
            json.dumps(pool, sort_keys=True).encode()
        ).hexdigest(),
        'standalone_get_status': get_status,
        'calls': len(rows),
        'correct': sum(r['error'] is None for r in rows),
        'p50_ms': statistics.median(times),
        'p95_ms': times[math.ceil(0.95 * len(times)) - 1],
        'workloads': workloads,
        'pool': pool,
        'measurements': rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ('measurements', 'pool')},
            indent=2,
        )
    )
    if report['correct'] != report['calls']:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?', default='http://127.0.0.1:8000/mcp')
    parser.add_argument(
        '--output', type=Path, default=ROOT / 'evaluation/reports/mcp-final.json'
    )
    parser.add_argument(
        '--allow-get-stream',
        action='store_true',
        help='Record baseline GET violation without aborting the latency comparison.',
    )
    args = parser.parse_args()
    asyncio.run(run(args.url, args.output, args.allow_get_stream))
