"""Independent release-review oracles; does not modify candidate tests or code."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from search import Catalog
from test_query import garment


class IndependentReleaseReview(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog([
            garment('001', price=1600, description='Plain dress', color='Black'),
            garment('002', price=900, description='Black and white print dress', color='White'),
            garment('003', price=400, kind='Bag', color='Black'),
            garment('004', price=900, kind='Skirt'),
            garment('005', price=400, kind='Sandals', category='Shoes'),
        ])

    def response(self, query, **arguments):
        plan = self.catalog.parser.parse(query)
        payload = self.catalog.search({'query': query, **arguments})
        print(json.dumps({'query': query, 'arguments': arguments,
                          'actual_plan': asdict(plan), 'response': payload}))
        return payload

    def test_mixed_primary_choices_survive_suffix(self):
        for connector in ('plus', 'and'):
            for enabled in (True, False):
                with self.subTest(connector=connector, recommendations=enabled):
                    payload = self.response(
                        f'dress {connector} skirt with a bag to match',
                        include_recommendations=enabled)
                    self.assertEqual({p['id'] for p in payload['results']},
                                     {'001', '002', '004'})

    def test_conjoined_color_print_stays_primary(self):
        payload = self.response(
            'dress with a black and white print and a bag to match',
            include_recommendations=True)
        self.assertEqual(payload['results'], [{'id': '002'}])
        self.assertEqual([r['id'] for r in payload['recommendations']], ['003'])

    def test_attribute_scope_cannot_move_primary_budget(self):
        payload = self.response(
            'dress with a black and white print under 1000 and a bag under 500 to match',
            include_recommendations=True)
        self.assertTrue(all(self.catalog.by_id[p['id']]['price']['amount'] <= 1000
                            for p in payload['results']))
        self.assertEqual(payload['results'], [{'id': '002'}])
        self.assertEqual([r['id'] for r in payload['recommendations']], ['003'])


class BoundaryIntentEvidenceTests(unittest.TestCase):
    def test_coordinated_attribute_requires_complete_source_evidence(self):
        catalog = Catalog([
            garment('001', color='Black', description='Black floral print dress'),
            garment('002', color='White', description='Black and white print dress'),
            garment('003', color='White', description='White floral print dress'),
            garment('004', kind='Bag', price=400),
        ])
        query = 'dress with a black and white print and a bag to match'
        plan = catalog.parser.parse(query)
        self.assertEqual(plan.primary[0].types, ('Dress',))
        self.assertEqual(plan.primary[0].phrases, ('black and white print',))
        self.assertIn('Bag', plan.complements[0].types)
        payload = catalog.search({'query': query, 'include_recommendations': True})
        self.assertEqual(payload['results'], [{'id': '002'}])
        self.assertEqual([r['id'] for r in payload['recommendations']], ['004'])
        self.assertEqual(payload['recommendations'][0]['for_product_id'], '002')

    def test_missing_compound_attribute_does_not_broaden_search(self):
        catalog = Catalog([
            garment('001', color='Black', description='Black floral print dress'),
            garment('002', color='White', description='White floral print dress'),
            garment('003', kind='Bag'),
        ])
        payload = catalog.search({
            'query': 'dress with a black and white print and a bag to match',
            'include_recommendations': True})
        self.assertEqual(payload, {'results': [], 'recommendations': []})

    def test_attachment_preserves_independent_primary_and_accessory_filters(self):
        catalog = Catalog([
            garment('001', price=900),
            garment('002', kind='Skirt', price=1200),
            garment('003', kind='Bag', price=400),
        ])
        query = 'dress under 1000 plus skirt under 1300 with a bag under 500 to match'
        plan = catalog.parser.parse(query)
        self.assertEqual([i.types for i in plan.primary], [('Dress',), ('Skirt',)])
        self.assertEqual([i.filters for i in plan.primary],
                         [{'max_price': 1000}, {'max_price': 1300}])
        self.assertEqual(plan.complements[0].filters, {'max_price': 500})
        payload = catalog.search({'query': query, 'include_recommendations': True})
        self.assertEqual({p['id'] for p in payload['results']}, {'001', '002'})
        self.assertEqual([r['id'] for r in payload['recommendations']], ['003'])
        self.assertIn(payload['recommendations'][0]['for_product_id'], {'001', '002'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
