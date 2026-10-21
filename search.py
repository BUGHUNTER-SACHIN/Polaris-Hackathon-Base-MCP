"""Catalog-grounded lexical retrieval with exact filtering and ordering."""

from collections import defaultdict
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError
from query import QueryParser, audience_matches, words
from recommendations import recommend

ROOT = Path(__file__).resolve().parent
INPUT_SCHEMA = json.loads((ROOT / 'schemas/input.schema.json').read_text())
OUTPUT_SCHEMA = json.loads((ROOT / 'schemas/output.schema.json').read_text())
VALIDATOR = Draft202012Validator(INPUT_SCHEMA)
STRING_FILTERS = ('category', 'product_type', 'color', 'audience', 'section', 'pattern')


def validate_arguments(arguments):
    # Reject non-JSON floating point values even when called directly from Python.
    json.dumps(arguments, allow_nan=False)
    try:
        VALIDATOR.validate(arguments)
    except ValidationError as exc:
        raise ValueError(exc.message) from exc
    filters = arguments.get('filters', {})
    if any(not filters[k].strip() for k in STRING_FILTERS if k in filters):
        raise ValueError('String filters cannot be blank')
    if filters.get('min_price', 0) > filters.get('max_price', math.inf):
        raise ValueError('min_price cannot exceed max_price')


@lru_cache(maxsize=2048)
def tokens(text):
    return tuple(re.findall(r'\w+', text.casefold()))


class Catalog:
    def __init__(self, products):
        self.products = sorted(products, key=lambda p: p['id'])
        self.by_id = {p['id']: p for p in self.products}
        self.postings = defaultdict(set)
        self.name_words = {}
        self.facets = {field: defaultdict(set) for field in STRING_FILTERS}
        for p in self.products:
            self.name_words[p['id']] = frozenset(tokens(p['name']))
            words = set(
                tokens(
                    ' '.join(
                        str(p.get(k) or '')
                        for k in ('name', 'description', *STRING_FILTERS)
                    )
                )
            )
            for word in words:
                self.postings[word].add(p['id'])
            for field in STRING_FILTERS:
                self.facets[field][str(p.get(field) or '').strip().casefold()].add(
                    p['id']
                )
        self.parser = QueryParser(
            {p['product_type'] for p in self.products},
            {p.get('color', '') for p in self.products},
            {p.get('pattern', '') for p in self.products},
        )
        self.orders = {
            ('id', False): self.products,
            ('id', True): list(reversed(self.products)),
        }
        for field, key in (
            ('price', lambda p: p['price']['amount']),
            ('review_count', lambda p: p['rating']['count']),
        ):
            for reverse in (False, True):
                self.orders[field, reverse] = sorted(
                    self.products, key=key, reverse=reverse
                )
        rated = [p for p in self.products if p['rating']['average'] is not None]
        unrated = [p for p in self.products if p['rating']['average'] is None]
        for reverse in (False, True):
            self.orders['rating', reverse] = (
                sorted(rated, key=lambda p: p['rating']['average'], reverse=reverse)
                + unrated
            )

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding='utf-8')))

    def relevance(self, product, query_tokens):
        """IDF-weighted field evidence plus a contiguous product-name phrase boost."""
        if not all(
            product['id'] in self.postings.get(word, ()) for word in query_tokens
        ):
            return 0
        name_words = self.name_words[product['id']]
        score = 1.0
        type_words = set(tokens(product['product_type']))
        for word in query_tokens:
            idf = math.log1p(
                len(self.products) / (1 + len(self.postings.get(word, ())))
            )
            score += idf * (1 + 3 * (word in name_words) + 2 * (word in type_words))
        if len(query_tokens) > 1:
            phrase = ' '.join(query_tokens)
            if phrase in ' '.join(tokens(product['name'])):
                score += 3.0
        return score

    def intent_score(self, product, intent):
        score = self.relevance(product, intent.terms)
        score += sum(
            0.5 for word in intent.soft if product['id'] in self.postings.get(word, ())
        )
        # A named type in the source name is stronger evidence than description-only.
        name = set(words(product['name']))
        score += sum(0.25 for term in words(product['product_type']) if term in name)
        if product['product_type'] in intent.types:
            score += 0.5 / (1 + intent.types.index(product['product_type']))
        return score

    def recommend(self, results, arguments):
        return recommend(self, results, arguments)

    def retrieve(self, intent, explicit):
        """Intersect full postings before ranking; recheck original catalog facts."""
        if not intent.meaningful or intent.unsupported:
            return []
        inferred = dict(intent.filters)
        if explicit.get('min_price', 0) > inferred.get('max_price', math.inf):
            inferred.pop('max_price', None)
        if explicit.get('max_price', math.inf) < inferred.get('min_price', 0):
            inferred.pop('min_price', None)
        filters = {**inferred, **explicit}
        pools = [
            self.facets[k].get(v.strip().casefold(), set())
            for k, v in filters.items()
            if k in STRING_FILTERS
        ]
        types = intent.types
        if 'category' in explicit and types:
            category_ids = self.facets['category'].get(
                explicit['category'].strip().casefold(), set()
            )
            if not any(
                category_ids.intersection(
                    self.facets['product_type'].get(t.casefold(), set())
                )
                for t in types
            ):
                types = ()  # An explicit category overrides a conflicting inferred type.
        for field, values in (
            ('product_type', types),
            ('color', intent.colors),
            ('pattern', intent.patterns),
        ):
            if values and field not in explicit:
                pools.append(
                    set().union(
                        *(self.facets[field].get(v.casefold(), set()) for v in values)
                    )
                )
        terms = intent.terms
        if (
            'product_type' in explicit
            and intent.types
            and explicit['product_type'].strip().casefold()
            not in [t.casefold() for t in intent.types]
        ):
            terms = tuple(t for t in terms if t != 'jeans')
        pools.extend(self.postings.get(word, set()) for word in terms)
        pools.sort(key=len)
        ids = set(pools[0]).intersection(*pools[1:]) if pools else self.by_id.keys()
        candidates = []
        for id in sorted(ids):
            p = self.by_id[id]
            if not self.matches(p, filters):
                continue
            if 'audience' not in explicit and not audience_matches(p, intent.audience):
                continue
            if 'color' not in explicit and p.get('color') in intent.excluded_colors:
                continue
            if any(id in self.postings.get(t, ()) for t in intent.excluded_terms):
                continue
            candidates.append(p)
        return candidates

    def exact_page(self, arguments):
        """Walk a preordered full catalog, stopping only after the exact requested page."""
        filters = arguments.get('filters', {})
        pools = [
            self.facets[k].get(v.strip().casefold(), set())
            for k, v in filters.items()
            if k in STRING_FILTERS
        ]
        pools.sort(key=len)
        if pools and not pools[0]:
            return []
        field = arguments.get('sort_by', 'relevance')
        descending = arguments.get('sort_order', 'desc') == 'desc'
        if field == 'relevance':
            field, descending = 'id', False
        start, limit = int(arguments.get('offset', 0)), int(arguments.get('limit', 10))
        found, results = 0, []
        for p in self.orders[field, descending]:
            if any(p['id'] not in pool for pool in pools) or not self.matches(
                p, filters
            ):
                continue
            if found >= start:
                results.append({'id': p['id']})
                if len(results) == limit:
                    break
            found += 1
        return results

    @staticmethod
    def matches(product, filters):
        for key in STRING_FILTERS:
            if (
                key in filters
                and str(product.get(key) or '').strip().casefold()
                != filters[key].strip().casefold()
            ):
                return False
        price = product['price']['amount']
        average = product['rating']['average']
        return (
            price >= filters.get('min_price', 0)
            and price <= filters.get('max_price', math.inf)
            and (
                'min_rating' not in filters
                or (average is not None and average >= filters['min_rating'])
            )
            and product['rating']['count'] >= filters.get('min_review_count', 0)
        )

    def search(self, arguments):
        validate_arguments(arguments)
        query_text = arguments.get('query', '').strip()
        query = bool(query_text)
        if not query:
            results = self.exact_page(arguments)
            return {
                'results': results,
                'recommendations': self.recommend(results, arguments),
            }
        filters = arguments.get('filters', {})
        scores = {}
        plan = self.parser.parse(query_text)
        if len(plan.primary) == 1:
            intent = plan.primary[0]
            candidates = self.retrieve(intent, filters)
            scores = {p['id']: self.intent_score(p, intent) for p in candidates}
        else:
            # Rank each choice independently; equal branch ranks share a score.
            # This supplies coverage without making the order depend on page size.
            for intent in plan.primary:
                branch = self.retrieve(intent, filters)
                branch.sort(key=lambda p: self.intent_score(p, intent), reverse=True)
                for rank, p in enumerate(branch, 1):
                    scores[p['id']] = max(scores.get(p['id'], 0), 1 / (60 + rank))
            candidates = [self.by_id[id] for id in sorted(scores)]
        sort_by = arguments.get('sort_by', 'relevance')
        reverse = arguments.get('sort_order', 'desc') == 'desc'
        # Stable sort preserves ascending ID for equal keys, in either direction.
        if sort_by == 'relevance':
            candidates.sort(key=lambda p: scores[p['id']], reverse=reverse)
        elif sort_by == 'rating':
            rated = [p for p in candidates if p['rating']['average'] is not None]
            unrated = [p for p in candidates if p['rating']['average'] is None]
            rated.sort(key=lambda p: p['rating']['average'], reverse=reverse)
            candidates = rated + unrated
        else:
            key = {
                'id': lambda p: p['id'],
                'price': lambda p: p['price']['amount'],
                'review_count': lambda p: p['rating']['count'],
            }[sort_by]
            candidates.sort(key=key, reverse=reverse)
        offset, limit = int(arguments.get('offset', 0)), int(arguments.get('limit', 10))
        results = [{'id': p['id']} for p in candidates[offset : offset + limit]]
        return {
            'results': results,
            'recommendations': (
                self.recommend(results, arguments)
                if results and arguments.get('include_recommendations', False)
                else []
            ),
        }
