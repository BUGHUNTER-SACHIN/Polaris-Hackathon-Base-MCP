import unittest

from search import Catalog
from test_query import garment


class RankingTests(unittest.TestCase):
    def test_name_and_phrase_evidence(self):
        c = Catalog(
            [
                garment('001', name='Evening dress', description='Wide leg cotton'),
                garment('002', name='Cotton dress'),
                garment('003', name='Cotton wide dress', description='Wide leg cotton'),
                garment('004', name='Wide leg cotton dress'),
            ]
        )
        ids = lambda query: [p['id'] for p in c.search({'query': query})['results']]
        self.assertLess(
            ids('cotton dress').index('002'), ids('cotton dress').index('001')
        )
        self.assertEqual(ids('wide leg dress')[0], '004')
        self.assertEqual(ids('titanium dress'), [])

    def test_mixed_coverage_pagination_and_field_sort(self):
        c = Catalog(
            [
                garment(
                    str(i).zfill(3), kind='Dress' if i < 7 else 'Bag', price=i * 100
                )
                for i in range(1, 13)
            ]
        )
        args = {'query': 'dress and bag', 'limit': 4}
        page = c.search(args)['results']
        self.assertEqual(
            {c.by_id[p['id']]['product_type'] for p in page[:2]}, {'Dress', 'Bag'}
        )
        self.assertEqual(
            c.search({**args, 'offset': 2, 'limit': 2})['results'], page[2:]
        )
        self.assertEqual(
            c.search({**args, 'sort_by': 'price', 'sort_order': 'asc'})['results'],
            [{'id': str(i).zfill(3)} for i in range(1, 5)],
        )
        self.assertEqual(
            c.search({**args, 'filters': {'product_type': 'Dress'}})['recommendations'],
            [],
        )
        self.assertEqual(len({p['id'] for p in page}), len(page))

    def test_mixed_constraints_and_ties(self):
        c = Catalog(
            [
                garment('001'),
                garment('002', kind='Shirt', color='White'),
                garment('003', kind='Shirt'),
                garment('004', color='White'),
            ]
        )
        out = c.search({'query': 'black dresses and white shirts', 'sort_order': 'asc'})
        self.assertEqual([r['id'] for r in out['results']], ['001', '002'])

    def test_integral_json_numbers_follow_schema(self):
        c = Catalog([garment('001'), garment('002')])
        self.assertEqual(
            c.search({'limit': 1.0, 'offset': 1.0})['results'], [{'id': '002'}]
        )
