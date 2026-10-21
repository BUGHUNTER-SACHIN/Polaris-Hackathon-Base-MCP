"""Local, catalog-grounded proxy evaluation; never contacts the organizer or an LLM."""

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from search import Catalog, OUTPUT_SCHEMA  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402


def matches_expected(p, rule):
    for key, field in [
        ('types', 'product_type'),
        ('colors', 'color'),
        ('patterns', 'pattern'),
    ]:
        if key in rule and p[field] not in rule[key]:
            return False
    if p['price']['amount'] > rule.get('max_price', math.inf):
        return False
    text = ' '.join(str(p.get(f) or '') for f in ('name', 'description')).casefold()
    if not all(t in text for t in rule.get('text', [])):
        return False
    if rule.get('audience') == 'men':
        return p['audience'] == 'Menswear' or p['section'].startswith(
            ('Men ', 'Mens ', 'Denim Men')
        )
    return True


def oracle(products, args):
    """Independent empty-query oracle, deliberately not Catalog.matches."""
    f = args.get('filters', {})
    selected = []
    for p in products:
        if any(
            str(p.get(k) or '').strip().casefold() != v.strip().casefold()
            for k, v in f.items()
            if k
            in ('color', 'category', 'product_type', 'audience', 'section', 'pattern')
        ):
            continue
        amount, rating = p['price']['amount'], p['rating']['average']
        if not f.get('min_price', 0) <= amount <= f.get('max_price', math.inf):
            continue
        if 'min_rating' in f and (rating is None or rating < f['min_rating']):
            continue
        if p['rating']['count'] < f.get('min_review_count', 0):
            continue
        selected.append(p)
    selected.sort(key=lambda p: p['id'])
    field = args.get('sort_by', 'relevance')
    desc = args.get('sort_order', 'desc') == 'desc'
    if field == 'rating':
        selected = sorted(
            (p for p in selected if p['rating']['average'] is not None),
            key=lambda p: p['rating']['average'],
            reverse=desc,
        ) + [p for p in selected if p['rating']['average'] is None]
    elif field != 'relevance':
        key = {
            'id': lambda p: p['id'],
            'price': lambda p: p['price']['amount'],
            'review_count': lambda p: p['rating']['count'],
        }[field]
        selected.sort(key=key, reverse=desc)
    start = args.get('offset', 0)
    return [p['id'] for p in selected[start : start + args.get('limit', 10)]]


def ndcg(grades, slots):
    # Fixed grade-3 ceiling, like the brief; rule grades are local proxies.
    dcg = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(grades[:slots]))
    return dcg / sum(7 / math.log2(i + 2) for i in range(slots))


def peak_memory_mib():
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
                (n, ctypes.c_size_t)
                for n in (
                    'PeakWorkingSetSize',
                    'WorkingSetSize',
                    'QuotaPeakPagedPoolUsage',
                    'QuotaPagedPoolUsage',
                    'QuotaPeakNonPagedPoolUsage',
                    'QuotaNonPagedPoolUsage',
                    'PagefileUsage',
                    'PeakPagefileUsage',
                )
            ]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        process = ctypes.windll.kernel32.GetCurrentProcess
        process.restype = wintypes.HANDLE
        get = ctypes.windll.psapi.GetProcessMemoryInfo
        get.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if get(process(), ctypes.byref(counters), counters.cb):
            return counters.PeakWorkingSetSize / 1024**2
        return None
    import resource

    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / (1024**2 if sys.platform == 'darwin' else 1024)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=('dev', 'heldout', 'all'), default='dev')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--repeats', type=int, default=3)
    options = parser.parse_args()
    start = time.perf_counter()
    catalog = Catalog.load(ROOT / 'data/products.json')
    startup = time.perf_counter() - start
    by_id = {p['id']: p for p in catalog.products}
    cases_path = Path(__file__).with_name('cases.json')
    cases = json.loads(cases_path.read_text())
    rows = []
    for case in cases:
        if options.split != 'all' and case['split'] != options.split:
            continue
        args = case['args']
        timings, error, result = [], None, None
        for _ in range(options.repeats):
            start = time.perf_counter()
            try:
                result = catalog.search(args)
            except ValueError as exc:
                error = type(exc).__name__
            timings.append((time.perf_counter() - start) * 1000)
        row = {
            'name': case['name'],
            'area': case['area'],
            'split': case['split'],
            'median_ms': statistics.median(timings),
            'error': error,
        }
        if case.get('invalid'):
            row['pass'] = error is not None
        elif error:
            row['pass'] = False
        else:
            Draft202012Validator(OUTPUT_SCHEMA).validate(result)
            ids = [p['id'] for p in result['results']]
            rec_ids = [p['id'] for p in result['recommendations']]
            structural = (
                len(ids) == len(set(ids))
                and len(ids) <= args.get('limit', 10)
                and len(rec_ids) == len(set(rec_ids))
                and not set(ids) & set(rec_ids)
                and all(i in by_id for i in ids + rec_ids)
                and all(r['for_product_id'] in ids for r in result['recommendations'])
            )
            row.update(result=result, pass_structure=structural)
            if case.get('exact'):
                row['pass'] = (
                    structural and ids == oracle(catalog.products, args) and not rec_ids
                )
            elif case.get('empty'):
                row['pass'] = structural and not ids and not rec_ids
            else:
                choices = case['choices']
                grades = [
                    (
                        3
                        if any(matches_expected(by_id[i], rule) for rule in choices)
                        else 0
                    )
                    for i in ids
                ]
                coverage = sum(
                    any(matches_expected(by_id[i], rule) for i in ids)
                    for rule in choices
                ) / len(choices)
                row.update(proxy_ndcg10=ndcg(grades, 10), choice_coverage=coverage)
                passed = (
                    structural
                    and bool(ids)
                    and all(g == 3 for g in grades)
                    and coverage == 1
                )
                if 'complements' in case:
                    rg = [
                        (
                            3
                            if any(
                                matches_expected(by_id[i], rule)
                                for rule in case['complements']
                            )
                            else 0
                        )
                        for i in rec_ids
                    ]
                    row['proxy_complement_ndcg5'] = ndcg(rg, 5)
                    passed = passed and bool(rec_ids) and all(g == 3 for g in rg)
                if case.get('no_recommendations'):
                    passed = passed and not rec_ids
                row['pass'] = passed
        rows.append(row)
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['area']].append(row)
    report = {
        'note': 'Student-authored rule-based proxies; not Bedrock grades or an official score.',
        'split': options.split,
        'cases_sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        'startup_seconds': startup,
        'peak_process_mib': peak_memory_mib(),
        'passed': sum(r['pass'] for r in rows),
        'total': len(rows),
        'areas': {
            area: {
                'passed': sum(r['pass'] for r in rs),
                'total': len(rs),
                'mean_proxy_ndcg10': statistics.mean(
                    [r.get('proxy_ndcg10', 0) for r in rs]
                ),
            }
            for area, rs in grouped.items()
        },
        'cases': rows,
    }
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))


if __name__ == '__main__':
    main()
