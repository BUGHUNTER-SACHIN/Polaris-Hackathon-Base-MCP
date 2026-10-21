"""Evidence-driven language regressions, independent of hidden benchmark cases."""

import unittest

from evaluation.quality import evaluate
from search import Catalog
from test_query import garment


class QualityParsingTests(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog(
            [
                garment("0001", price=1500, color="Black"),
                garment("0002", price=2500, color="Black"),
                garment(
                    "0003", price=900, color="White", description="Off shoulder cotton"
                ),
                garment("0004", price=900, color="Off White"),
                garment("0005", kind="Bag", color="White", price=700),
                garment("0006", kind="Skirt", price=800),
            ]
        )

    def ids(self, query, **arguments):
        return [
            p["id"]
            for p in self.catalog.search({"query": query, **arguments})["results"]
        ]

    def test_request_verbs_keep_unknown_facts(self):
        for prefix in ("recommend", "suggest"):
            with self.subTest(prefix=prefix):
                self.assertTrue(self.ids(prefix + " a black dress"))
                self.assertEqual(self.ids(prefix + " a titanium dress"), [])
        self.assertEqual(self.ids("recommend something"), [])

    def test_choice_markers_are_not_catalog_requirements(self):
        for marker in ("both", "either"):
            query = marker + " a dress and a bag"
            result = self.catalog.search({"query": query})["results"]
            self.assertEqual(
                {self.catalog.by_id[p["id"]]["product_type"] for p in result},
                {"Dress", "Bag"},
            )

    def test_budget_phrases_are_prices(self):
        for phrase in (
            "within INR 2000",
            "with a budget of INR 2000",
            "no more than INR 2000",
            "within a budget of 2000",
            "budget of 2k",
        ):
            with self.subTest(phrase=phrase):
                self.assertEqual(self.ids("black dress " + phrase), ["0001"])
        plan = self.catalog.parser.parse("dress no less than 1600")
        self.assertEqual(plan.primary[0].filters, {"min_price": 1600})

    def test_result_units_are_not_money(self):
        query = "black dress no more than 1 result cheapest first"
        self.assertEqual(self.ids(query), ["0001"])
        plan = self.catalog.parser.parse(query)
        self.assertEqual(plan.primary[0].filters, {})
        self.assertEqual(plan.limit, 1)

    def test_hyphenated_colors_and_negations(self):
        self.assertEqual(self.ids("off-white dress"), ["0004"])
        self.assertNotIn("0004", self.ids("dress avoid off-white"))
        self.assertEqual(self.ids("off-white dress made of adamantium"), [])

    def test_hyphenated_pattern(self):
        c = Catalog([garment("001", pattern="Dot"), garment("002", pattern="Solid")])
        result = c.search({"query": "polka-dot dress"})
        self.assertEqual(result["results"], [{"id": "001"}])

    def test_rating_units_do_not_become_money_or_choices(self):
        self.catalog.by_id["0001"]["rating"]["average"] = 4.5
        self.catalog.by_id["0002"]["rating"]["average"] = 3
        for phrase in ("rated 4 stars and above", "4+ stars", "4 stars and above"):
            with self.subTest(phrase=phrase):
                plan = self.catalog.parser.parse("black dress " + phrase)
                self.assertEqual(plan.primary[0].filters, {"min_rating": 4})
                self.assertEqual(self.ids("black dress " + phrase), ["0001"])

    def test_review_unit_and_explicit_precedence(self):
        plan = self.catalog.parser.parse("dress within 2000 with at least 5 reviews")
        self.assertEqual(
            plan.primary[0].filters, {"max_price": 2000, "min_review_count": 5}
        )
        self.assertEqual(
            self.ids("black dress no more than 1000", filters={"min_price": 2000}),
            ["0002"],
        )

    def test_small_reference_pool_does_not_require_fabricated_fill(self):
        catalog = Catalog(
            [
                garment("0001", kind="Skirt", description="Floral embroidery"),
                garment("0002", kind="Skirt", description="Plain cotton"),
            ]
        )
        arguments = {"query": "floral skirt", "limit": 10}
        payload = catalog.search(arguments)
        self.assertEqual(payload, {"results": [{"id": "0001"}], "recommendations": []})
        case = {
            "args": arguments,
            "choices": [{"types": ["Skirt"], "text": ["floral"]}],
            "min_results": 1,
            "reference_count": 1,
        }
        evaluate(case, payload, catalog)
        with self.assertRaisesRegex(AssertionError, "reference count"):
            evaluate({**case, "reference_count": 2}, payload, catalog)


if __name__ == "__main__":
    unittest.main()
