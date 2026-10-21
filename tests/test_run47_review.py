"""Independent adversarial review oracles; failures are release blockers.

Expected IDs are derived from fixture facts and the public contract, not parser
internals. In particular, unsupported accessory requests cannot erase a valid
primary when recommendations are disabled. Do not weaken these assertions.
"""

import unittest

from jsonschema import Draft202012Validator

from search import Catalog, OUTPUT_SCHEMA
from test_query import garment


class Run47AdversarialReviewTests(unittest.TestCase):
    def setUp(self):
        self.c = Catalog([
            garment('0001', price=900,
                    description='Cotton dress with sleeves and a shirt collar'),
            garment('0002', price=900, description='Plain cotton dress'),
            garment('0003', color='White', price=1300),
            garment('0004', color='Red', price=1800),
            garment('0010', kind='Bag', color='White', price=400,
                    category='Accessories'),
            garment('0011', kind='Bag', color='Black', price=1400,
                    category='Accessories', description='Bag with a laptop compartment'),
            garment('0012', kind='Bag', color='Red', price=600,
                    category='Accessories'),
            garment('0013', kind='Bag', color='White', price=400,
                    category='Accessories',
                    rating={'average': None, 'count': 0, 'synthetic': True}),
            garment('0020', kind='Sandals', color='Red', price=500,
                    category='Shoes'),
            garment('0021', kind='Sandals', color='White', price=500,
                    category='Shoes'),
            garment('0030', kind='Shirt', color='White', price=800,
                    audience='Menswear', section='Men Shirts',
                    description='Cotton shirt with a shirt collar'),
            garment('0040', kind='Hoodie', color='Grey', price=1000),
            garment('0041', kind='Hoodie', color='Grey', price=1200),
            garment('0042', kind='Hoodie', color='Black', price=800,
                    description='Padded shell'),
        ])

    def search(self, text, **args):
        result = self.c.search({'query': text, **args})
        Draft202012Validator(OUTPUT_SCHEMA).validate(result)
        ids = [p['id'] for p in result['results']]
        recs = result['recommendations']
        rec_ids = [p['id'] for p in recs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(rec_ids), len(set(rec_ids)))
        self.assertTrue(set(ids + rec_ids) <= self.c.by_id.keys())
        self.assertFalse(set(ids) & set(rec_ids))
        self.assertTrue(all(p['for_product_id'] in ids for p in recs))
        return result

    def ids(self, result):
        return [p['id'] for p in result['results']]

    def rec_ids(self, result):
        return {p['id'] for p in result['recommendations']}

    def test_plus_scoped_prices_colors_and_field_ties(self):
        query = 'black dress under 1000 plus white bag under 500'
        for order, expected in (
            ('asc', ['0010', '0013', '0001', '0002']),
            ('desc', ['0001', '0002', '0010', '0013']),
        ):
            with self.subTest(order=order):
                args = {'sort_by': 'price', 'sort_order': order}
                full = self.search(query, **args)
                self.assertEqual(self.ids(full), expected)
                self.assertEqual(self.ids(self.search(query, offset=1, limit=2,
                                                      **args)), expected[1:3])

    def test_explicit_filters_override_conflicting_plus_prose(self):
        result = self.search(
            'red dress plus white bag under 500',
            filters={'color': 'Black', 'min_price': 500, 'max_price': 1500},
            sort_by='price', sort_order='asc',
        )
        self.assertEqual(self.ids(result), ['0001', '0002', '0011'])

    def test_unknown_explicit_category_stays_empty(self):
        result = self.search('dress plus bag',
                             filters={'category': 'Laptops'},
                             include_recommendations=True)
        self.assertEqual(result, {'results': [], 'recommendations': []})

    def test_excluded_category_is_not_filled_back_in(self):
        result = self.search('dress plus bag excluding accessories')
        self.assertEqual(set(self.ids(result)), {'0001', '0002', '0003', '0004'})

    def test_impossible_plus_choice_does_not_relax_its_budget(self):
        result = self.search('red dress under 0 plus white bag under 500')
        self.assertEqual(self.ids(result), ['0010', '0013'])

    def test_irrelevant_and_unavailable_requests_stay_empty(self):
        for query in ('comfy laptop', 'dress plus spaceship engine',
                      'comfy unobtainium hoodie', 'I would love !!!',
                      'I would love a titanium dress', 'dress plus size M'):
            with self.subTest(query=query):
                self.assertEqual(self.search(query),
                                 {'results': [], 'recommendations': []})

    def test_polite_prefix_preserves_quantity_material_and_budget(self):
        result = self.search("I’d love 2 black cotton dresses under 1000")
        self.assertEqual(set(self.ids(result)), {'0001', '0002'})

    def test_love_inside_a_catalog_product_name_is_preserved(self):
        catalog = Catalog([
            garment('0007', name='Love slogan dress'),
            garment('0008', name='Plain dress'),
        ])
        for query in ('love slogan dress', 'I would love a love slogan dress'):
            with self.subTest(query=query):
                result = catalog.search({'query': query})
                self.assertEqual(result['results'], [{'id': '0007'}])

    def test_comfy_does_not_remove_explicit_material_or_exclusion(self):
        result = self.search('comfy cotton hoodies under 1100 avoid black')
        self.assertEqual(self.ids(result), ['0040'])

    def test_rating_nulls_and_id_ties_with_plus(self):
        for direction in ('asc', 'desc'):
            result = self.search('dress plus bag', sort_by='rating',
                                 sort_order=direction, limit=100)
            ids = self.ids(result)
            self.assertEqual(ids[-1], '0013')
            self.assertEqual(ids[:-1], sorted(ids[:-1]))
        rated = self.search('dress plus bag', filters={'min_rating': 4})
        self.assertNotIn('0013', self.ids(rated))

    def test_invalid_arguments_remain_errors(self):
        for filters in ({'min_price': 2000, 'max_price': 500}, {'min_rating': 6}):
            with self.subTest(filters=filters), self.assertRaises(ValueError):
                self.search('I would love dress plus bag', filters=filters)

    def test_suffix_range_is_not_a_choice_separator(self):
        result = self.search('dress with a bag between 300 and 700 to match',
                             include_recommendations=True)
        self.assertEqual(set(self.ids(result)), {'0001', '0002', '0003', '0004'})
        self.assertEqual(self.rec_ids(result), {'0010', '0012', '0013'})

    def test_suffix_color_alternatives_remain_accessory_constraints(self):
        result = self.search('dress with a black or white bag to match',
                             include_recommendations=True)
        self.assertEqual(set(self.ids(result)), {'0001', '0002', '0003', '0004'})
        self.assertEqual(self.rec_ids(result), {'0010', '0011', '0013'})

    def test_suffix_cannot_discard_a_primary_shirt_collar_requirement(self):
        result = self.search('dress with a shirt collar and a bag to match',
                             include_recommendations=True)
        self.assertEqual(self.ids(result), ['0001'])
        self.assertTrue(result['recommendations'])

    def test_suffix_unavailable_accessory_does_not_erase_primary(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                result = self.search('dress with a bag in stock to match',
                                     include_recommendations=enabled)
                self.assertEqual(set(self.ids(result)),
                                 {'0001', '0002', '0003', '0004'})
                self.assertEqual(result['recommendations'], [])

    def test_suffix_unsupported_category_does_not_erase_primary(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                result = self.search('dress with a laptop to match',
                                     include_recommendations=enabled)
                self.assertEqual(set(self.ids(result)),
                                 {'0001', '0002', '0003', '0004'})
                # A laptop-compartment bag is not a laptop.
                self.assertEqual(result['recommendations'], [])

    def test_suffix_negative_accessory_type_is_not_a_positive_choice(self):
        result = self.search('dress with a bag and no sandals to match',
                             include_recommendations=True)
        self.assertEqual(set(self.ids(result)), {'0001', '0002', '0003', '0004'})
        self.assertEqual(self.rec_ids(result), {'0010', '0011', '0012', '0013'})

    def test_recommendation_coverage_respects_constraints_and_references(self):
        result = self.search('dress with a matching white bag under 500 and sandals under 600',
                             filters={'color': 'Black', 'max_price': 1000},
                             include_recommendations=True, offset=1, limit=1)
        self.assertEqual(self.ids(result), ['0002'])
        self.assertEqual(self.rec_ids(result), {'0010', '0013', '0020', '0021'})
        self.assertTrue(all(r['for_product_id'] == '0002'
                            for r in result['recommendations']))

    def test_recommendation_coverage_does_not_force_substitutes(self):
        result = self.search('dress with a matching dress and sandals under 0',
                             include_recommendations=True)
        self.assertTrue(result['results'])
        self.assertEqual(result['recommendations'], [])

    def test_recommendation_category_exclusion_is_not_filled_back_in(self):
        result = self.search('dress with a matching bag excluding accessories',
                             include_recommendations=True)
        self.assertTrue(result['results'])
        self.assertEqual(result['recommendations'], [])

    def test_recommendation_color_exclusions_and_budgets_are_hard(self):
        result = self.search(
            'dress with a matching bag excluding white under 700 '
            'and sandals excluding white under 700',
            include_recommendations=True,
        )
        self.assertEqual(self.rec_ids(result), {'0012', '0020'})


if __name__ == '__main__':
    unittest.main()
