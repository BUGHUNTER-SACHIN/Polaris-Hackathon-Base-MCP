import unittest

from query import QueryParser, audience_matches
from search import Catalog
from test_search import product


def garment(id, kind='Dress', color='Black', price=1000, **values):
    p = product(
        id, price, 4, 2, color=color, name=kind, description='Soft cotton jersey'
    )
    p.update(product_type=kind, category='Garment Full body', audience='Ladieswear')
    p.update(values)
    return p


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.c = Catalog(
            [
                garment('001'),
                garment('002', color='Red', price=500),
                garment('003', price=2500),
                garment(
                    '004',
                    kind='Shirt',
                    color='White',
                    section='Men Shirts',
                    audience='Menswear',
                ),
                garment('005', kind='Sneakers', category='Shoes'),
                garment('006', kind='Trousers', name='Blue jeans', color='Dark Blue'),
            ]
        )

    def ids(self, query, **args):
        return [p['id'] for p in self.c.search({'query': query, **args})['results']]

    def test_sentences_and_money(self):
        self.assertEqual(
            self.ids('I am looking for a black dress under INR 2,000'), ['001']
        )
        self.assertEqual(self.ids('black dresses up to 2k rupees'), ['001'])
        self.assertEqual(self.ids('dress between 600 and 2000'), ['001'])
        self.assertEqual(self.ids('dress under INR 0'), [])

    def test_explicit_constraints_override_prose(self):
        self.assertEqual(
            self.ids(
                'red dress under 500', filters={'color': 'Black', 'max_price': 2000}
            ),
            ['001'],
        )
        self.assertEqual(
            self.ids(
                'black dress', filters={'product_type': 'Shirt', 'color': 'White'}
            ),
            ['004'],
        )
        self.assertEqual(
            self.ids('dress under 100', filters={'min_price': 2000}), ['003']
        )
        self.assertEqual(
            self.ids('black dress', filters={'category': 'Shoes'}), ['005']
        )

    def test_unknown_requirements_are_not_discarded(self):
        for text in (
            'Nike sneakers',
            'dress made of unobtainium',
            'spaceship engine',
            'quantum dress',
        ):
            self.assertEqual(self.ids(text), [], text)

    def test_inventory_and_size_requests_need_unavailable_evidence(self):
        for text in (
            'dress in stock',
            'dress size M',
            'discounted dress',
            'dress with free shipping',
        ):
            self.assertEqual(self.ids(text), [], text)

    def test_typo_and_color_alias(self):
        self.assertEqual(self.ids('black sneekers'), ['005'])
        self.assertEqual(self.ids('navy jeans'), ['006'])

    def test_audience_from_section(self):
        self.assertEqual(self.ids('white shirts for men'), ['004'])
        self.assertEqual(self.ids('white shirts for women'), [])

    def test_exclusion(self):
        self.assertEqual(self.ids('dress not red'), ['001', '003'])
        self.assertEqual(self.ids('dress without cotton'), [])

    def test_complement_does_not_constrain_primary_when_disabled(self):
        self.assertEqual(
            self.ids('dress with a matching bag under 10'), ['001', '002', '003']
        )

    def test_budget_and_audience_scope(self):
        plan = self.c.parser.parse('black jeans and white shirts under 2000 for men')
        self.assertEqual(len(plan.primary), 2)
        self.assertTrue(
            all(
                i.filters['max_price'] == 2000 and i.audience == 'men'
                for i in plan.primary
            )
        )
        plan = self.c.parser.parse('dress under 2000 with a matching bag under 1000')
        self.assertEqual(plan.primary[0].filters['max_price'], 2000)
        self.assertEqual(plan.complements[0].filters['max_price'], 1000)
        plan = self.c.parser.parse('dress under 2000 with a matching bag above 3000')
        self.assertEqual(plan.complements[0].filters, {'min_price': 3000})

    def test_per_choice_audiences(self):
        plan = self.c.parser.parse('dresses for women and shirts for men')
        self.assertIsNone(plan.audience)
        self.assertEqual([i.audience for i in plan.primary], ['women', 'men'])

    def test_multiple_accessory_intents(self):
        plan = self.c.parser.parse(
            'dress with a matching bag under 1000 and belt under 500'
        )
        self.assertEqual(len(plan.complements), 2)
        self.assertEqual(
            [i.filters['max_price'] for i in plan.complements], [1000, 500]
        )
