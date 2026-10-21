import itertools
import unittest

from evaluation.run import oracle
from search import Catalog, OUTPUT_SCHEMA
from jsonschema import Draft202012Validator
from test_search import product


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.products = [
            product(
                str(i).zfill(5),
                [0, 500, 999][i % 3],
                None if i % 4 == 0 else [1, 3.5, 5][i % 3],
                i % 5,
                color='Black' if i % 2 else 'White',
                description=None if i % 3 == 0 else 'Soft cotton',
            )
            for i in range(35)
        ]
        self.c = Catalog(self.products)

    def test_exact_pages_all_directions_and_fields(self):
        filters = [
            {},
            {'color': ' BLACK '},
            {'category': 'garment upper body', 'min_price': 500},
            {
                'min_price': 500,
                'max_price': 999,
                'min_rating': 3.5,
                'min_review_count': 2,
            },
            {
                'product_type': 'vest top',
                'audience': 'LADIESWEAR',
                'section': 'Basics',
                'pattern': 'Solid',
            },
            {'color': 'unknown'},
            {'min_rating': 5},
            {'min_review_count': 0},
        ]
        for f, sort, order, offset in itertools.product(
            filters,
            ('relevance', 'id', 'price', 'rating', 'review_count'),
            ('asc', 'desc'),
            (0, 4, 10000),
        ):
            args = dict(
                query=' \t ',
                filters=f,
                sort_by=sort,
                sort_order=order,
                offset=offset,
                limit=7,
            )
            with self.subTest(args=args):
                r = self.c.search(args)
                Draft202012Validator(OUTPUT_SCHEMA).validate(r)
                self.assertEqual(
                    [x['id'] for x in r['results']], oracle(self.products, args)
                )

    def test_invalid_values(self):
        cases = [
            None,
            [],
            True,
            {'query': 42},
            {'query': 'x' * 1001},
            {'filters': None},
            {'include_recommendations': 1},
            {'offset': True},
            {'offset': 10001},
            {'offset': 1.2},
            {'limit': 101},
            {'limit': None},
            {'sort_order': 'ASC'},
            {'filters': {'category': []}},
            {'filters': {'unknown': 'x'}},
            {'filters': {'min_price': -1}},
            {'filters': {'min_rating': 0}},
            {'filters': {'min_rating': 5.1}},
            {'filters': {'min_review_count': True}},
            {'filters': {'min_review_count': 1.5}},
            {'filters': {'pattern': '\t'}},
            {'filters': {'min_price': float('inf')}},
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.c.search(args)

    def test_punctuation_is_not_empty_query(self):
        self.assertEqual(self.c.search({'query': '!!! 😃'})['results'], [])

    def test_inclusive_bounds_and_nulls(self):
        for price in (0, 500, 999):
            actual = self.c.search(
                {'filters': {'min_price': price, 'max_price': price}, 'limit': 100}
            )
            self.assertEqual(
                len(actual['results']),
                sum(p['price']['amount'] == price for p in self.products),
            )
        actual = self.c.search({'filters': {'min_rating': 1}, 'limit': 100})
        self.assertTrue(
            all(
                self.c.by_id[p['id']]['rating']['average'] is not None
                for p in actual['results']
            )
        )

    def test_mixed_ties_stay_id_ascending_for_both_directions(self):
        for order in ('asc', 'desc'):
            args = {
                'query': 'cotton top',
                'sort_by': 'price',
                'sort_order': order,
                'limit': 100,
            }
            ids = [p['id'] for p in self.c.search(args)['results']]
            for _, group in itertools.groupby(
                ids, key=lambda id: self.c.by_id[id]['price']['amount']
            ):
                group = list(group)
                self.assertEqual(group, sorted(group))
