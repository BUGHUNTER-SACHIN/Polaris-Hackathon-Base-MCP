"""Semantic intent and catalog-evidence checks for the structural revision."""

from dataclasses import asdict
import unittest

from evaluation.run47 import evaluate_case
from search import Catalog
from test_query import garment
import test_run47_review as review


class MatchingScopeTests(unittest.TestCase):
    def setUp(self):
        fixture = review.Run47AdversarialReviewTests(
            'test_suffix_range_is_not_a_choice_separator')
        fixture.setUp()
        self.c = fixture.c

    def test_primary_and_complement_have_independent_ranges(self):
        q = 'dress between 900 and 1400 with a bag between 300 and 700 to match'
        plan = self.c.parser.parse(q)
        self.assertEqual(len(plan.primary), 1)
        self.assertEqual(plan.primary[0].types, ('Dress',))
        self.assertEqual(plan.primary[0].filters, {'min_price': 900, 'max_price': 1400})
        self.assertEqual(plan.complements[0].filters, {'min_price': 300, 'max_price': 700})
        result = self.c.search({'query': q, 'include_recommendations': True})
        self.assertEqual({p['id'] for p in result['results']}, {'0001', '0002', '0003'})
        self.assertEqual({r['id'] for r in result['recommendations']}, {'0010', '0012', '0013'})
        self.assertTrue(all(r['for_product_id'] in {'0001', '0002', '0003'}
                            for r in result['recommendations']))

    def test_primary_attributes_have_type_and_phrase_evidence(self):
        q = 'dress with a shirt collar and a bag to match'
        p = self.c.parser.parse(q)
        self.assertEqual(p.primary[0].types, ('Dress',))
        self.assertEqual(p.primary[0].phrases, ('shirt collar',))
        self.assertTrue({'shirt', 'collar'} <= set(p.primary[0].terms))
        self.assertIn('Bag', p.complements[0].types)
        self.assertNotIn('Shirt', p.complements[0].types)
        self.assertEqual(self.c.search({'query': q})['results'], [{'id': '0001'}])

    def test_attribute_grammar_generalizes_beyond_the_collar_example(self):
        c = Catalog([
            garment('001', description='Dress with shirt sleeves'),
            garment('002', description='Plain dress'),
            garment('003', kind='Shirt', description='Shirt sleeves'),
            garment('004', kind='Bag'),
        ])
        q = 'dress with shirt sleeves and a bag to match'
        p = c.parser.parse(q)
        self.assertEqual(p.primary[0].types, ('Dress',))
        self.assertEqual(p.primary[0].phrases, ('shirt sleeves',))
        r = c.search({'query': q, 'include_recommendations': True})
        self.assertEqual(r['results'], [{'id': '001'}])
        self.assertEqual([p['id'] for p in r['recommendations']], ['004'])

    def test_source_words_without_the_attribute_phrase_do_not_suffice(self):
        c = Catalog([
            garment('001', description='Dress with a shirt collar'),
            garment('002', description='Shirt layered under a dress with a collar'),
        ])
        self.assertEqual(c.search({'query': 'dress with a shirt collar'})['results'],
                         [{'id': '001'}])

    def test_unknown_primary_material_is_not_moved_into_accessories(self):
        q = 'dress with an unobtainium blend and a bag to match'
        p = self.c.parser.parse(q)
        self.assertIn('unobtainium', p.primary[0].terms)
        self.assertEqual(self.c.search({'query': q, 'include_recommendations': True}),
                         {'results': [], 'recommendations': []})

    def test_primary_garment_parts_are_not_opaque_accessory_items(self):
        for part in ('hood', 'zip', 'slit', 'embroidery', 'design'):
            with self.subTest(part=part):
                c = Catalog([
                    garment('001', description='Dress with a ' + part),
                    garment('002', description='Plain dress'),
                    garment('003', kind='Bag'),
                ])
                q = 'dress with a ' + part + ' and a bag to match'
                p = c.parser.parse(q)
                self.assertIn(part, p.primary[0].terms)
                r = c.search({'query': q, 'include_recommendations': True})
                self.assertEqual(r['results'], [{'id': '001'}])
                self.assertEqual([r['id'] for r in r['recommendations']], ['003'])

    def test_color_alternatives_and_exclusions_stay_in_complement_scope(self):
        p = self.c.parser.parse('dress with a black or white bag to match')
        self.assertEqual(set(p.complements[0].colors), {'Black', 'White'})
        self.assertFalse(p.primary[0].colors)
        q = 'dress with a bag and no black and white to match'
        p = self.c.parser.parse(q)
        self.assertEqual(len(p.complements), 1)
        self.assertEqual(set(p.complements[0].excluded_colors), {'Black', 'White'})
        r = self.c.search({'query': q, 'include_recommendations': True})
        self.assertEqual({p['id'] for p in r['recommendations']}, {'0012'})

    def test_unsupported_complements_keep_scope_and_do_not_substitute(self):
        for target, expected_types in (('a laptop', ()), ('a bag in stock', ('Bag',))):
            q = 'dress with ' + target + ' to match'
            p = self.c.parser.parse(q)
            self.assertEqual(p.primary[0].types, ('Dress',))
            self.assertTrue(p.complements[0].unsupported)
            if expected_types:
                self.assertIn('Bag', p.complements[0].types)
            else:
                self.assertFalse(p.complements[0].types)
            for enabled in (False, True):
                r = self.c.search({'query': q, 'include_recommendations': enabled})
                self.assertEqual({p['id'] for p in r['results']},
                                 {'0001', '0002', '0003', '0004'})
                self.assertEqual(r['recommendations'], [])

    def test_negative_accessory_type_is_a_constraint_not_a_new_choice(self):
        p = self.c.parser.parse('dress with a bag and no sandals to match')
        self.assertEqual(len(p.complements), 1)
        self.assertIn('Bag', p.complements[0].types)
        self.assertEqual(p.complements[0].excluded_types, ('Sandals',))


class EvaluationFailureDiagnosticsTests(unittest.IsolatedAsyncioTestCase):
    async def test_call_schema_and_constraint_errors_remain_failed_rows(self):
        c = Catalog([garment('0001')])
        case = {'name': 'diagnostics', 'area': 'ranking', 'split': 'dev',
                'args': {'query': 'dress'}, 'min_results': 1,
                'choices': [{'types': ['Dress']}]}

        async def unavailable(args):
            raise TimeoutError('local test timeout')

        async def bad_schema(args):
            return {'results': [{'id': '0001'}]}

        async def unknown_id(args):
            return {'results': [{'id': 'missing'}], 'recommendations': []}

        for call, kind in ((unavailable, 'TimeoutError'),
                           (bad_schema, 'ValidationError'), (unknown_id, 'AssertionError')):
            row = await evaluate_case(case, c, call, c.parser)
            self.assertFalse(row['pass'])
            self.assertEqual(row['query'], 'dress')
            self.assertEqual(row['error_type'], kind)
            self.assertTrue(row['timed_tool_call'])
            self.assertIsInstance(row['milliseconds'], float)
            self.assertEqual(row['expected_intent']['choices'], case['choices'])
            self.assertEqual(row['actual_parsed_intent'], asdict(c.parser.parse('dress')))
            self.assertIn('result_ids', row)
        self.assertEqual(row['result_ids'], ['missing'])


if __name__ == '__main__':
    unittest.main()
