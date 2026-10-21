"""Regressions from public, user-authored live requests; no hidden cases."""

import json
from pathlib import Path
import unittest

from search import Catalog
from test_query import garment

CASES = json.loads(
    (Path(__file__).resolve().parents[1] / 'evaluation/advanced_cases.json').read_text()
)


class ParsingRemediationTests(unittest.TestCase):
    def setUp(self):
        products = [
            garment('0002', price=999),
            garment('0003', price=1200),
            garment('dress-x', price=800),
            garment('0004', color='Red', price=1500),
            garment('0006', color='Dark Blue', price=1800),
        ]
        for i, kind, color in (
            (10, 'Top', 'Black'),
            (12, 'Top', 'Dark Blue'),
            (14, 'Trousers', 'Beige'),
            (16, 'Trousers', 'Grey'),
            (18, 'Sneakers', 'White'),
            (20, 'Sandals', 'Beige'),
        ):
            p = garment(str(i).zfill(4), kind=kind, color=color, price=i * 80)
            p['name'] = f'{color} {kind}'
            products.append(p)
        for i, color, rating in (
            (22, 'White', 4.5),
            (24, 'Grey', 4),
            (26, 'Off White', 5),
            (28, 'White', None),
            (30, 'White', 3),
        ):
            p = garment(
                str(i).zfill(4),
                kind='Sneakers',
                color=color,
                price=i * 70,
                audience='Menswear',
                section='Men Shoes',
            )
            p['rating']['average'] = rating
            products.append(p)
        self.c = Catalog(products)

    def test_result_count_is_not_a_price(self):
        plan = self.c.parser.parse('dress under 2000 at most 10 results')
        self.assertEqual(plan.primary[0].filters, {'max_price': 2000})
        self.assertEqual(plan.limit, 10)
        self.assertTrue(
            self.c.search({'query': 'dress under 2000 at most 10 results'})['results']
        )

    def test_avoid_color_and_multiword_type(self):
        r = self.c.search({'query': 'dress avoid black'})
        self.assertTrue(r['results'])
        self.assertTrue(
            all(self.c.by_id[p['id']]['color'] != 'Black' for p in r['results'])
        )
        plan = self.c.parser.parse('shoes excluding sneakers')
        self.assertIn('Sneakers', plan.primary[0].excluded_types)
        plan = self.c.parser.parse('dress avoid dark blue')
        self.assertEqual(plan.primary[0].excluded_colors, ('Dark Blue',))

    def test_rating_reviews_and_quantities_are_not_money(self):
        plan = self.c.parser.parse(
            '2 dresses under 2000 rated at least 4.8 with at least 10,000 reviews'
        )
        self.assertEqual(
            plan.primary[0].filters,
            {'max_price': 2000, 'min_rating': 4.8, 'min_review_count': 10000},
        )
        self.assertEqual(plan.primary[0].quantity, 2)

    def test_parity_precedes_sorting_pagination_and_keeps_zeros(self):
        args = {
            'query': 'dress with even-numbered product IDs',
            'sort_by': 'price',
            'sort_order': 'asc',
        }
        rows = self.c.search(args)['results']
        self.assertTrue(rows)
        self.assertTrue(
            all(
                p['id'].isascii() and p['id'].isdigit() and int(p['id']) % 2 == 0
                for p in rows
            )
        )
        self.assertIn({'id': '0002'}, rows)
        self.assertEqual(
            self.c.search({**args, 'offset': 1, 'limit': 2})['results'], rows[1:3]
        )
        counted = self.c.search({'query': '2 dresses with even-numbered product IDs'})[
            'results'
        ]
        self.assertEqual(len(counted), 2)
        self.assertTrue(all(int(p['id']) % 2 == 0 for p in counted))

    def test_original_seven_prompts(self):
        for case in CASES:
            n = case['test']
            with self.subTest(test=n):
                r = self.c.search(case['arguments'])
                ps = [self.c.by_id[p['id']] for p in r['results']]
                if n == 1:
                    self.assertTrue(ps)
                    self.assertTrue(
                        all(
                            p['id'].isdigit()
                            and int(p['id']) % 2 == 0
                            and p['color'] == 'Black'
                            and p['price']['amount'] <= 2000
                            for p in ps
                        )
                    )
                elif n == 2:
                    self.assertTrue(ps)
                    self.assertTrue(
                        all(
                            p['color'] in ('White', 'Grey')
                            and p['audience'] == 'Menswear'
                            and p['rating']['average'] >= 4
                            and p['price']['amount'] <= 3500
                            for p in ps
                        )
                    )
                elif n == 3:
                    self.assertEqual(len(ps), 6)
                    self.assertEqual(sum(p['product_type'] == 'Top' for p in ps), 2)
                    self.assertEqual(
                        sum(p['product_type'] == 'Trousers' for p in ps), 2
                    )
                    self.assertEqual(
                        sum(p['product_type'] in ('Sneakers', 'Sandals') for p in ps), 2
                    )
                    self.assertEqual(len({p['name'] for p in ps}), 6)
                else:
                    self.assertEqual(r, {'results': [], 'recommendations': []})

    def test_explicit_arguments_and_unknown_evidence_remain_authoritative(self):
        r = self.c.search(
            {
                'query': 'dress avoid black at most 2 results cheapest first',
                'filters': {'color': 'Black'},
                'sort_by': 'price',
                'sort_order': 'desc',
                'limit': 1,
            }
        )
        self.assertEqual(r['results'], [{'id': '0003'}])
        self.assertEqual(
            self.c.search({'query': 'black titanium dress at most 10 results'})[
                'results'
            ],
            [],
        )

    def test_query_controls_sort_and_limit_without_explicit_arguments(self):
        r = self.c.search(
            {'query': 'dress under 2000 show at most 2 results cheapest first'}
        )
        self.assertEqual([p['id'] for p in r['results']], ['dress-x', '0002'])

    def test_recommendation_exclusions_and_current_page_reference(self):
        c = Catalog(
            [
                garment('001', kind='Shirt', audience='Menswear', section='Men Shirts'),
                garment(
                    '002', kind='Sneakers', audience='Menswear', section='Men Shoes'
                ),
                garment(
                    '003', kind='Other shoe', audience='Menswear', section='Men Shoes'
                ),
            ]
        )
        r = c.search(
            {
                'query': 'shirt for men with matching shoes under 2000 excluding sneakers',
                'include_recommendations': True,
                'limit': 1,
            }
        )
        self.assertTrue(r['results'])
        self.assertTrue(r['recommendations'])
        for rec in r['recommendations']:
            self.assertIn({'id': rec['for_product_id']}, r['results'])
            self.assertNotEqual(c.by_id[rec['id']]['product_type'], 'Sneakers')
            self.assertLessEqual(c.by_id[rec['id']]['price']['amount'], 2000)

    def test_parity_applies_to_recommendations_too(self):
        c = Catalog(
            [
                garment('0002'),
                garment('0003', kind='Bag'),
                garment('bag-x', kind='Bag'),
                garment('0004', kind='Bag'),
            ]
        )
        r = c.search(
            {
                'query': 'dress with even-numbered product IDs',
                'include_recommendations': True,
            }
        )
        self.assertEqual([p['id'] for p in r['recommendations']], ['0004'])

    def test_conditional_rating_keeps_nulls_but_explicit_rating_does_not(self):
        q = 'white sneakers for men with a rating of at least 4.0 if ratings are available'
        ids = {p['id'] for p in self.c.search({'query': q})['results']}
        self.assertIn('0028', ids)
        self.assertNotIn('0030', ids)
        ids = {
            p['id']
            for p in self.c.search({'query': q, 'filters': {'min_rating': 4}})[
                'results'
            ]
        }
        self.assertNotIn('0028', ids)

    def test_excluded_catalog_category_and_multiple_colors(self):
        plan = self.c.parser.parse('dress excluding Garment Full body')
        self.assertEqual(plan.primary[0].excluded_categories, ('Garment Full body',))
        self.assertEqual(
            self.c.search({'query': 'dress excluding Garment Full body'})['results'], []
        )
        r = self.c.search({'query': 'dress avoid black or red'})
        self.assertTrue(r['results'])
        self.assertTrue(
            all(self.c.by_id[p['id']]['color'] == 'Dark Blue' for p in r['results'])
        )

    def test_nonuniform_quantities_and_college_preference(self):
        c = Catalog(
            [
                garment(
                    '001',
                    kind='Top',
                    name='Child top',
                    audience='Children Sizes 92-140',
                    section='Young Girl',
                ),
                garment('002', kind='Top', name='Adult top'),
                garment('003', kind='Top', name='Other adult top'),
                garment('004', kind='Skirt', name='Adult skirt'),
            ]
        )
        q = "I'm building a wardrobe for college. Find 2 tops and 1 skirt. Give me a varied set of options."
        r = c.search({'query': q})['results']
        self.assertEqual(len(r), 3)
        self.assertNotIn({'id': '001'}, r)
        self.assertEqual(c.search({'query': q, 'limit': 100})['results'], r)
        self.assertEqual(sum(c.by_id[p['id']]['product_type'] == 'Top' for p in r), 2)
        for offset in (0, 1, 2):
            self.assertEqual(
                c.search({'query': q, 'offset': offset, 'limit': 1})['results'],
                r[offset : offset + 1],
            )

    def test_rating_and_quantity_prefixes_do_not_become_prices(self):
        for q in ('at least 2 dresses under 2000', 'exactly 2 dresses under 2000'):
            plan = self.c.parser.parse(q)
            self.assertEqual(plan.primary[0].quantity, 2)
            self.assertEqual(plan.primary[0].filters, {'max_price': 2000})
        plan = self.c.parser.parse('at least 4 stars dress under 2000')
        self.assertIsNone(plan.primary[0].quantity)
        self.assertEqual(plan.primary[0].filters, {'min_rating': 4, 'max_price': 2000})

    def test_mixed_rating_propagation_does_not_rescan_it_as_money(self):
        plan = self.c.parser.parse(
            'dress and bag rated at least 4.8 with at least 1,000 reviews'
        )
        for intent in plan.primary:
            self.assertEqual(
                intent.filters, {'min_rating': 4.8, 'min_review_count': 1000}
            )
