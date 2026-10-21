import unittest

from search import Catalog
from test_query import garment


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.c = Catalog(
            [
                garment('001'),
                garment('002', kind='Bag', price=500),
                garment('003', kind='Bag', price=1500),
                garment(
                    '004',
                    kind='Bag',
                    price=400,
                    audience='Menswear',
                    section='Men Accessories',
                ),
                garment('005', color='Red'),
                garment('006', kind='Belt', price=250),
                garment('007', kind='Bag', price=750, color='White'),
            ]
        )

    def search(self, query, **kwargs):
        return self.c.search(
            {'query': query, 'include_recommendations': True, **kwargs}
        )

    def test_scoped_budget_and_primary_filters(self):
        r = self.search(
            'dress under 2000 with a matching bag under 1000',
            filters={'product_type': 'Dress', 'color': 'Red'},
        )
        self.assertEqual(r['results'], [{'id': '005'}])
        self.assertEqual({x['id'] for x in r['recommendations']}, {'002', '007'})
        self.assertTrue(all(x['for_product_id'] == '005' for x in r['recommendations']))

    def test_current_page_references_and_unique_ids(self):
        r = self.search('dress with a matching bag', offset=1, limit=1)
        self.assertEqual(r['results'], [{'id': '005'}])
        self.assertTrue(all(x['for_product_id'] == '005' for x in r['recommendations']))
        self.assertEqual(
            len(r['recommendations']), len({x['id'] for x in r['recommendations']})
        )

    def test_do_not_force_substitutes_or_impossible_accessory(self):
        for query in (
            'dress with a matching dress',
            'dress with a matching bag under 0',
            'dress with a matching titanium bag',
            'spaceship with a matching bag',
        ):
            self.assertEqual(self.search(query)['recommendations'], [], query)

    def test_disabled_complement_ignored_and_mixed_in_primary(self):
        r = self.search('dress with a matching bag', include_recommendations=False)
        self.assertTrue(
            all(self.c.by_id[p['id']]['product_type'] == 'Dress' for p in r['results'])
        )
        self.assertEqual(r['recommendations'], [])
        mixed = self.c.search({'query': 'dress and bag'})
        self.assertEqual(
            {self.c.by_id[p['id']]['product_type'] for p in mixed['results']},
            {'Dress', 'Bag'},
        )

    def test_generic_complement_and_audience(self):
        r = self.search('dress for women')
        self.assertTrue(r['recommendations'])
        self.assertNotIn('004', {x['id'] for x in r['recommendations']})
        self.assertTrue(
            all(
                self.c.by_id[x['id']]['product_type'] in ('Bag', 'Belt')
                for x in r['recommendations']
            )
        )

    def test_unqualified_budget_applies_to_generic_recommendations(self):
        r = self.search('dress under 1200')
        self.assertTrue(r['recommendations'])
        self.assertTrue(
            all(
                self.c.by_id[x['id']]['price']['amount'] <= 1200
                for x in r['recommendations']
            )
        )
