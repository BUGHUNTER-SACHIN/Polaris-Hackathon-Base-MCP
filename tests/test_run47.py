"""Observed language/coverage regressions; no hidden benchmark expectations."""

import unittest

from search import Catalog
from test_query import garment


class Run47RegressionTests(unittest.TestCase):
    def setUp(self):
        products = [
            garment('0001'),
            garment('0002', kind='Skirt', color='Red'),
            garment('0003', kind='Hoodie'),
            garment('0004', kind='Sandals', color='Red', category='Shoes'),
            garment('0005', kind='Belt'),
        ]
        products += [garment(f'01{i:02}', kind='Bag', color='White') for i in range(8)]
        self.c = Catalog(products)

    def search(self, text, **args):
        return self.c.search({'query': text, **args})

    def test_plus_keeps_choice_constraints_and_pagination(self):
        query = 'a black dress plus a white bag under 1500'
        result = self.search(query)
        types = {self.c.by_id[r['id']]['product_type'] for r in result['results']}
        self.assertEqual(types, {'Dress', 'Bag'})
        self.assertEqual(self.search(query, offset=2, limit=3)['results'], result['results'][2:5])
        self.assertEqual(self.search('dress plus a spaceship engine')['results'], [])

    def test_polite_request_prefix_preserves_unknown_attributes(self):
        self.assertEqual(self.search('I would love a red skirt')['results'], [{'id': '0002'}])
        self.assertEqual(self.search('I would love a titanium skirt')['results'], [])
        self.assertEqual(self.search('love slogan skirt')['results'], [])

    def test_comfy_is_a_soft_preference_with_unknown_terms_preserved(self):
        self.assertTrue(self.search('something comfy for a lazy Sunday')['results'])
        plan = self.c.parser.parse('something comfy for a lazy Sunday')
        self.assertNotIn('comfy', plan.primary[0].terms)
        self.assertTrue(self.search('comfy titanium hoodie')['results'] == [])

    def test_suffix_complements_stay_out_of_primary_even_when_disabled(self):
        for query in ('a dress with a bag to match', 'a dress and a bag to go with it'):
            for enabled in (True, False):
                with self.subTest(query=query, enabled=enabled):
                    result = self.search(query, include_recommendations=enabled)
                    self.assertEqual(result['results'], [{'id': '0001'}])
                    self.assertEqual(bool(result['recommendations']), enabled)
                    self.assertTrue(all(self.c.by_id[r['id']]['product_type'] == 'Bag'
                                        for r in result['recommendations']))
        result = self.search('dress with a titanium bag to match', include_recommendations=True)
        self.assertEqual(result['results'], [{'id': '0001'}])
        self.assertEqual(result['recommendations'], [])

    def test_complement_choices_do_not_starve_each_other(self):
        query = 'dress with a matching bag and sandals'
        result = self.search(query, include_recommendations=True)
        recs = result['recommendations']
        self.assertEqual(len(recs), 5)
        self.assertEqual({self.c.by_id[r['id']]['product_type'] for r in recs}, {'Bag', 'Sandals'})
        self.assertEqual(len({r['id'] for r in recs}), 5)
        self.assertTrue(all(r['for_product_id'] == '0001' for r in recs))
        self.assertEqual(result, self.search(query, include_recommendations=True))

    def test_suffix_budget_and_exclusion_are_not_relaxed(self):
        result = self.search('dress with a white bag under 0 to match', include_recommendations=True)
        self.assertEqual(result['results'], [{'id': '0001'}])
        self.assertEqual(result['recommendations'], [])
        result = self.search('dress with a bag excluding white to match', include_recommendations=True)
        self.assertEqual(result['recommendations'], [])

    def test_suffix_keeps_primary_attribute_on_the_primary(self):
        catalog = Catalog([
            garment('001', description='Cotton dress with sleeves'),
            garment('002', description='Plain dress'),
            garment('003', kind='Bag'),
        ])
        result = catalog.search({
            'query': 'dress with sleeves and a bag to match',
            'include_recommendations': True,
        })
        self.assertEqual(result['results'], [{'id': '001'}])
        self.assertEqual([r['id'] for r in result['recommendations']], ['003'])


if __name__ == '__main__':
    unittest.main()
