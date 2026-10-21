import unittest

from search import Catalog, STRING_FILTERS, tokens
from test_search import product


class IndexTests(unittest.TestCase):
    def test_postings_preserve_scan_results(self):
        products = [
            product(
                str(i).zfill(4),
                i % 3 * 500,
                None if i % 5 == 0 else 4,
                i % 4,
                color='White' if i % 2 else 'Black',
                name='Cotton top' if i % 3 else 'Soft skirt',
                description=None if i % 7 == 0 else 'Soft cotton jersey',
            )
            for i in range(40)
        ]
        for i, p in enumerate(products):
            if i % 3 == 0:
                p['product_type'] = 'Skirt'
                p['category'] = 'Garment Lower body'
        catalog = Catalog(products)
        for q in ('cotton top', 'soft', 'COTTON jersey', 'skirt', 'spaceship', ''):
            for f in (
                {},
                {'color': ' black '},
                {'min_price': 500},
                {'color': 'unknown'},
            ):
                for direction in ('asc', 'desc'):
                    with self.subTest(query=q, filters=f, direction=direction):
                        words = tokens(q)
                        expected = []
                        for p in products:
                            text = set(
                                tokens(
                                    ' '.join(
                                        str(p.get(k) or '')
                                        for k in (
                                            'name',
                                            'description',
                                            *STRING_FILTERS,
                                        )
                                    )
                                )
                            )
                            if Catalog.matches(p, f) and all(w in text for w in words):
                                expected.append(p)
                        expected.sort(
                            key=lambda p: p['id'], reverse=direction == 'desc'
                        )
                        actual = catalog.search(
                            {
                                'query': q,
                                'filters': f,
                                'sort_by': 'id',
                                'sort_order': direction,
                                'offset': 2,
                                'limit': 10,
                            }
                        )
                        self.assertEqual(
                            [p['id'] for p in actual['results']],
                            [p['id'] for p in expected[2:12]],
                        )

    def test_missing_queries_do_not_grow_index(self):
        c = Catalog([product('001', 999, 4, 2)])
        sizes = (len(c.postings), len(c.facets['color']))
        c.search({'query': 'qzxmn', 'filters': {'color': 'missing'}})
        self.assertEqual(sizes, (len(c.postings), len(c.facets['color'])))
