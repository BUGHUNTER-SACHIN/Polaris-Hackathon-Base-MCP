"""Live local regressions, never an organizer benchmark or a query reformulator."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import re
import time

import httpx
from jsonschema import Draft202012Validator
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

ROOT = Path(__file__).resolve().parents[1]


def checks(number, payload, args, by_id):
    ids = [p['id'] for p in payload['results']]
    recs = payload['recommendations']
    rids = [p['id'] for p in recs]
    assert len(ids) == len(set(ids)) and len(rids) == len(set(rids))
    assert not set(ids) & set(rids)
    assert all(isinstance(i, str) and i in by_id for i in ids + rids)
    assert all(r['for_product_id'] in ids for r in recs)
    assert len(ids) <= args.get('limit', 10)
    ps = [by_id[i] for i in ids]
    if number == 1:
        assert 0 < len(ps) <= 10
        assert all(
            re.fullmatch('[0-9]+', p['id'])
            and int(p['id']) % 2 == 0
            and p['product_type'] == 'Dress'
            and p['color'] == 'Black'
            and p['price']['amount'] <= 2000
            for p in ps
        )
    elif number == 2:
        assert 0 < len(ps) <= 8
        for p in ps:
            assert p['product_type'] == 'Sneakers' and p['color'] in ('White', 'Grey')
            assert p['price']['amount'] <= 3500
            assert p['audience'] == 'Menswear' or p['section'].startswith(
                ('Men ', 'Mens ')
            )
            rating = p['rating']['average']
            assert rating is None or rating >= 4
            if 'min_rating' in args.get('filters', {}):
                assert rating is not None and rating >= 4
    elif number == 3:
        assert len(ps) == 6 and len({p['name'].strip().casefold() for p in ps}) == 6
        tops = [p for p in ps if p['product_type'] in ('Top', 'Vest top')]
        trousers = [p for p in ps if p['product_type'] == 'Trousers']
        shoes = [p for p in ps if p['category'] == 'Shoes']
        assert len(tops) == len(trousers) == len(shoes) == 2
        assert all(p['color'] in ('Black', 'Dark Blue') for p in tops)
        assert all(
            p['color']
            in (
                'Black',
                'White',
                'Off White',
                'Beige',
                'Light Beige',
                'Dark Beige',
                'Greyish Beige',
                'Grey',
                'Light Grey',
                'Dark Grey',
            )
            for p in trousers
        )
        assert all(p['price']['amount'] <= 2500 for p in ps)
        assert all(not p['audience'].startswith(('Children', 'Baby')) for p in ps)
    elif number == 8:
        assert 0 < len(ps) <= 3
        assert all(
            p['product_type'] == 'Dress'
            and p['color'] != 'Black'
            and p['price']['amount'] <= 2000
            for p in ps
        )
        assert ps == sorted(ps, key=lambda p: (p['price']['amount'], p['id']))
    elif number == 9:
        assert 0 < len(ps) <= 3
        assert all(
            p['category'] == 'Shoes'
            and p['product_type'] != 'Sneakers'
            and p['price']['amount'] <= 2500
            for p in ps
        )
    elif number == 10:
        assert ps and recs
        assert all(p['product_type'] == 'Shirt' for p in ps)
        assert all(
            by_id[i]['product_type'] == 'Other shoe'
            and by_id[i]['price']['amount'] <= 2000
            for i in rids
        )
    else:
        # 5/6 are safety/unsupported guards, not successful native outfit planning.
        assert not ps and not recs
    if number in (1, 2):
        assert ps == sorted(ps, key=lambda p: (p['price']['amount'], p['id']))
    if number != 10:
        assert not recs  # None of the supported original requests enables complements.


async def run(url, output):
    catalog_path = ROOT / 'data/products.json'
    catalog_sha = hashlib.sha256(catalog_path.read_bytes()).hexdigest()
    assert (
        catalog_sha
        == '05b6aa5e8e8c1c8c997d584f8288e432862454f8820531e13473443e83c8f073'
    )
    by_id = {p['id']: p for p in json.loads(catalog_path.read_text(encoding='utf-8'))}
    cases = json.loads(Path(__file__).with_name('advanced_cases.json').read_text())
    for number, query in (
        (8, 'dress under 2000 avoid black show at most 3 results cheapest first'),
        (9, 'shoes excluding sneakers under 2500 show at most 3 results'),
        (10, 'shirt for men with matching shoes under 2000 excluding sneakers'),
    ):
        cases.append(
            {
                'test': number,
                'arguments': {'query': query, 'include_recommendations': number == 10},
                'original_capability': 'supplementary_regression',
            }
        )
    input_schema = json.loads((ROOT / 'schemas/input.schema.json').read_text())
    output_schema = json.loads((ROOT / 'schemas/output.schema.json').read_text())
    validator = Draft202012Validator(output_schema)
    rows = []
    async with httpx.AsyncClient() as client:
        assert (
            await client.get(url, headers={'Accept': 'text/event-stream'})
        ).status_code == 405
    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            assert init.protocolVersion == '2025-11-25'
            tools = (await session.list_tools()).tools
            assert len(tools) == 1 and tools[0].name == 'search_products'
            assert (
                tools[0].inputSchema == input_schema
                and tools[0].outputSchema == output_schema
            )
            for case in cases:
                original = case['arguments']
                for mode, args in (
                    ('original_arguments', original),
                    (
                        'query_only',
                        {
                            'query': original['query'],
                            'include_recommendations': original.get(
                                'include_recommendations', False
                            ),
                        },
                    ),
                ):
                    row = {
                        'test': case['test'],
                        'mode': mode,
                        'arguments': args,
                        'capability': case['original_capability'],
                    }
                    start = time.perf_counter()
                    try:
                        response = await asyncio.wait_for(
                            session.call_tool('search_products', args), 10
                        )
                        assert not response.isError
                        data = response.structuredContent
                        validator.validate(data)
                        assert json.loads(response.content[0].text) == data
                        row['response'] = data
                        # Repeat each exact request: validate deterministic native output.
                        repeat = await asyncio.wait_for(
                            session.call_tool('search_products', args), 10
                        )
                        assert not repeat.isError and repeat.structuredContent == data
                        checks(case['test'], data, args, by_id)
                        row['pass'] = True
                    except (AssertionError, ValueError, TimeoutError) as exc:
                        row['error'] = type(exc).__name__ + ': ' + str(exc)
                        row['pass'] = False
                    row['pair_ms'] = (time.perf_counter() - start) * 1000
                    rows.append(row)
                    print(
                        json.dumps(
                            {
                                k: v
                                for k, v in row.items()
                                if k not in ('arguments', 'response')
                            }
                        )
                    )
    report = {
        'note': 'Exact public user prompts; local regression checks, not semantic judge scores. '
        'Safety passes for tests 5/6 do not count as native capability gains.',
        'url': url,
        'catalog_sha256': catalog_sha,
        'cases_sha256': hashlib.sha256(
            Path(__file__).with_name('advanced_cases.json').read_bytes()
        ).hexdigest(),
        'passed': sum(r['pass'] for r in rows),
        'total': len(rows),
        'cases': rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + '\n', encoding='utf-8'
    )
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))
    return report['passed'] == report['total']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    raise SystemExit(0 if asyncio.run(run(options.url, options.output)) else 1)
