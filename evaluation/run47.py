"""Additional frozen student proxies. No hidden queries or semantic judge scores."""

import argparse
import asyncio
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
import math
import re
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.quality import evaluate, satisfies  # noqa: E402
from search import Catalog, INPUT_SCHEMA, OUTPUT_SCHEMA  # noqa: E402
from query import QueryParser  # noqa: E402


def rule_matches(product, rule):
    source = ' '.join(re.findall(r'\w+',
        ((product.get('name') or '') + ' ' + (product.get('description') or '')).casefold()))
    return (satisfies(product, rule)
            and product['price']['amount'] >= rule.get('min_price', 0)
            and all(' ' + phrase + ' ' in ' ' + source + ' '
                    for phrase in rule.get('phrases', [])))


def check_plan(actual, expected, path='plan'):
    """Compare declared semantic expectations; unspecified diagnostics may vary."""
    if isinstance(expected, dict):
        for key, value in expected.items():
            assert key in actual, f'{path}.{key} missing'
            check_plan(actual[key], value, path + '.' + key)
    elif isinstance(expected, list) and all(isinstance(v, dict) for v in expected):
        assert len(actual) == len(expected), f'{path}: item scope count'
        for index, (a, e) in enumerate(zip(actual, expected)):
            check_plan(a, e, f'{path}[{index}]')
    elif isinstance(expected, list):
        assert sorted(actual) == sorted(expected), f'{path}: {actual!r} != {expected!r}'
    else:
        assert actual == expected, f'{path}: {actual!r} != {expected!r}'


def diagnostic_parser(catalog):
    if hasattr(catalog, 'parser'):
        return catalog.parser
    products = catalog.by_id.values()
    return QueryParser(
        {p['product_type'] for p in products},
        {p['color'] for p in products},
        {p['pattern'] for p in products},
        {p['category'] for p in products},
    )


async def evaluate_case(case, catalog, call, parser, *, remote=False):
    """Keep failures as failures, with their input, plan and any returned IDs."""
    start = time.perf_counter()
    row = {
        'name': case['name'], 'area': case['area'], 'split': case['split'],
        'arguments': case['args'], 'query': case['args'].get('query', ''),
        'expected_intent': {k: case[k] for k in (
            'choices', 'complements', 'empty', 'no_complements',
            'complement_coverage', 'expected_plan',
        ) if k in case},
        'actual_parsed_intent': None,
        'parsed_intent_source': ('local parser projection; MCP exposes no internal plan'
                                 if remote else 'actual local catalog parser'),
        'result_ids': [], 'recommendation_ids': [], 'pass': False,
        'timed_tool_call': False, 'milliseconds': None,
    }
    stage = 'parse'
    try:
        row['actual_parsed_intent'] = asdict(parser.parse(row['query']))
        stage = 'call'
        row['timed_tool_call'] = True
        call_start = time.perf_counter()
        try:
            payload = await call(case['args'])
        finally:
            row['milliseconds'] = (time.perf_counter() - call_start) * 1000
        row['response'] = payload
        if isinstance(payload, dict):
            for field, key in (('results', 'result_ids'),
                               ('recommendations', 'recommendation_ids')):
                if isinstance(payload.get(field), list):
                    row[key] = [p.get('id') for p in payload[field] if isinstance(p, dict)]
        stage = 'validate'
        evaluate(case, payload, catalog)
        if 'expected_plan' in case:
            check_plan(row['actual_parsed_intent'], case['expected_plan'])
        for field, rules in (('results', case.get('choices', [])),
                             ('recommendations', case.get('complements', []))):
            if rules:
                assert all(any(rule_matches(catalog.by_id[p['id']], rule)
                               for rule in rules) for p in payload[field]), field + ' constraints'
        if case.get('no_complements'):
            assert not payload['recommendations'], 'unsupported complement returned'
        if case.get('complement_coverage'):
            recs = [catalog.by_id[r['id']] for r in payload['recommendations']]
            assert all(any(rule_matches(p, rule) for p in recs)
                       for rule in case['complements']), 'missing complement choice'
        row['pass'] = True
    except Exception as exc:
        # This is a test harness: even an unexpected exception is a failed row,
        # never a successful empty tool response. Cancellation still propagates.
        row.update(error_type=type(exc).__name__, error=str(exc)[:2000], stage=stage)
    row['total_milliseconds'] = (time.perf_counter() - start) * 1000
    return row


async def run(options):
    cases_path = getattr(options, 'cases', None) or Path(__file__).with_name('run47_cases.json')
    raw = (ROOT / 'data/products.json').read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == '05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073'
    start = time.perf_counter()
    products = json.loads(raw)
    catalog = SimpleNamespace(by_id={p['id']: p for p in products}) if options.url else Catalog(products)
    startup = time.perf_counter() - start
    cases = [c for c in json.loads(cases_path.read_text())
             if options.split == 'all' or c['split'] == options.split]
    rows = []
    parser = diagnostic_parser(catalog)
    session_error = None

    async def measure(call):
        for case in cases:
            rows.append(await evaluate_case(case, catalog, call, parser,
                                            remote=bool(options.url)))

    if options.url:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                async with streamable_http_client(options.url, http_client=client) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        init = await session.initialize()
                        assert init.protocolVersion == '2025-11-25'
                        tools = (await session.list_tools()).tools
                        assert len(tools) == 1 and tools[0].name == 'search_products'
                        assert tools[0].inputSchema == INPUT_SCHEMA and tools[0].outputSchema == OUTPUT_SCHEMA

                        async def call(args):
                            result = await asyncio.wait_for(session.call_tool('search_products', args), 10)
                            assert not result.isError, 'MCP tool error: ' + str(result.content)[:1000]
                            assert json.loads(result.content[0].text) == result.structuredContent
                            return result.structuredContent

                        await measure(call)
        except Exception as exc:
            session_error = {'type': type(exc).__name__, 'message': str(exc)[:2000]}
            async def unavailable(args, error=exc):
                raise error
            for case in cases[len(rows):]:
                row = await evaluate_case(case, catalog, unavailable, parser, remote=True)
                row['stage'] = 'initialize_or_transport'
                row['timed_tool_call'] = False
                row['milliseconds'] = None
                rows.append(row)
    else:
        async def call(args):
            return catalog.search(args)
        await measure(call)
    groups = defaultdict(list)
    for row in rows:
        groups[row['area']].append(row)
    latencies = sorted(r['milliseconds'] for r in rows if r['timed_tool_call'])
    report = {'note': 'Student attribute/coverage proxies, not Bedrock grades or official scores. '
                      'Latency is this sequential case sample, not the official performance workload.',
              'url': options.url, 'split': options.split,
              'session_error': session_error,
              'catalog_sha256': digest, 'cases_sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
              'startup_seconds': startup, 'passed': sum(r['pass'] for r in rows), 'total': len(rows),
              'p95_ms': (latencies[math.ceil(.95 * len(latencies)) - 1]
                         if latencies else None),
              'areas': {k: {'passed': sum(r['pass'] for r in v), 'total': len(v)} for k, v in groups.items()},
              'cases': rows}
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))
    print('Failed cases:', [r['name'] for r in rows if not r['pass']])
    return report['passed'] == report['total'] and session_error is None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url')
    parser.add_argument('--cases', type=Path)
    parser.add_argument('--split', choices=('dev', 'heldout', 'all'), default='dev')
    parser.add_argument('--output', type=Path, required=True)
    raise SystemExit(0 if asyncio.run(run(parser.parse_args())) else 1)
