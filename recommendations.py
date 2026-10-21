"""Reviewed category relationships; all returned items still come from the catalog."""

from query import Intent, audience_matches, parity_matches

COMPATIBLE = {
    'Dress': (
        'Bag',
        'Belt',
        'Sandals',
        'Heeled sandals',
        'Pumps',
        'Earring',
        'Necklace',
    ),
    'Shirt': ('Trousers', 'Belt', 'Tie', 'Sneakers', 'Other shoe'),
    'Polo shirt': ('Trousers', 'Shorts', 'Belt', 'Sneakers'),
    'T-shirt': ('Trousers', 'Shorts', 'Sneakers', 'Bag'),
    'Top': ('Trousers', 'Skirt', 'Bag', 'Sandals'),
    'Vest top': ('Trousers', 'Skirt', 'Bag', 'Sandals'),
    'Blouse': ('Trousers', 'Skirt', 'Bag', 'Pumps'),
    'Trousers': ('Belt', 'Shirt', 'T-shirt', 'Sneakers', 'Blouse'),
    'Shorts': ('T-shirt', 'Vest top', 'Sneakers', 'Sandals'),
    'Skirt': ('Top', 'Vest top', 'Blouse', 'Sandals', 'Bag'),
    'Blazer': ('Shirt', 'Blouse', 'Trousers', 'Belt', 'Bag'),
    'Sweater': ('Trousers', 'Scarf', 'Boots', 'Bag'),
    'Cardigan': ('T-shirt', 'Top', 'Trousers', 'Bag'),
    'Hoodie': ('Trousers', 'Shorts', 'Sneakers'),
    'Jacket': ('Scarf', 'Hat/beanie', 'Boots', 'Gloves'),
    'Coat': ('Scarf', 'Hat/beanie', 'Boots', 'Gloves'),
    'Jumpsuit/Playsuit': ('Belt', 'Bag', 'Sandals', 'Earring'),
    'Swimsuit': ('Sarong', 'Sandals', 'Sunglasses', 'Bag'),
    'Bikini top': ('Swimwear bottom', 'Sarong', 'Sunglasses'),
    'Swimwear bottom': ('Bikini top', 'Swimwear top', 'Sarong'),
    'Sneakers': ('Socks',),
    'Boots': ('Socks', 'Scarf'),
    'Pyjama set': ('Slippers', 'Robe'),
}


def inferred_audience(product):
    for audience in ('baby', 'girls', 'boys', 'children', 'men', 'women'):
        if audience_matches(product, audience):
            return audience
    return None


def recommend(catalog, results, arguments):
    if not results or not arguments.get('include_recommendations', False):
        return []
    plan = catalog.parser.parse(arguments.get('query', ''))
    excluded = {r['id'] for r in results}
    ranked, seen_anchors, cache = {}, set(), {}
    choice_ids = [set() for _ in plan.complements]
    for result in results:
        anchor = catalog.by_id[result['id']]
        audience = plan.audience or inferred_audience(anchor)
        signature = (anchor['product_type'], anchor.get('color'), audience)
        if signature in seen_anchors:
            continue
        seen_anchors.add(signature)
        compatible = COMPATIBLE.get(anchor['product_type'], ())
        if not compatible:
            continue
        primary_intent = next(
            (
                i
                for i in plan.primary
                if not i.types or anchor['product_type'] in i.types
            ),
            plan.primary[0],
        )
        shared_budget = {
            k: v
            for k, v in primary_intent.filters.items()
            if k in ('min_price', 'max_price')
        }
        intents = plan.complements or [
            Intent(
                types=compatible,
                filters=shared_budget,
                audience=audience,
                meaningful=True,
            )
        ]
        for choice, intent in enumerate(intents):
            scoped_audience = intent.audience or audience
            types = tuple(t for t in (intent.types or compatible) if t in compatible)
            if not types:
                continue
            scoped = Intent(
                terms=intent.terms,
                types=types,
                colors=intent.colors,
                patterns=intent.patterns,
                filters=intent.filters,
                excluded_colors=intent.excluded_colors,
                excluded_terms=intent.excluded_terms,
                soft=intent.soft,
                audience=scoped_audience,
                meaningful=True,
                unsupported=intent.unsupported,
                excluded_types=intent.excluded_types,
                excluded_categories=intent.excluded_categories,
                nullable_rating=intent.nullable_rating,
                phrases=intent.phrases,
            )
            key = (
                types,
                scoped.terms,
                scoped.colors,
                scoped.patterns,
                tuple(sorted(scoped.filters.items())),
                scoped.excluded_colors,
                scoped.excluded_terms,
                scoped.soft,
                scoped_audience,
                scoped.excluded_types,
                scoped.excluded_categories,
                scoped.nullable_rating,
                scoped.phrases,
            )
            if key not in cache:
                cache[key] = [
                    (p, catalog.intent_score(p, scoped))
                    for p in catalog.retrieve(scoped, {})
                ]
            for p, base in cache[key]:
                if p['id'] in excluded or not parity_matches(p['id'], plan.id_parity):
                    continue
                if plan.complements:
                    choice_ids[choice].add(p['id'])
                score = base + (1 if p.get('color') == anchor.get('color') else 0)
                # Neutral catalog colors are a modest coordination preference.
                score += (
                    0.2
                    if p.get('color') in ('Black', 'White', 'Beige', 'Silver', 'Gold')
                    else 0
                )
                previous = ranked.get(p['id'])
                if previous is None or score > previous[0]:
                    ranked[p['id']] = (score, anchor['id'])
    ordered = sorted(ranked, key=lambda id: (-ranked[id][0], id))
    selected = set()
    # Reserve a best eligible match for each explicitly requested complement.
    # Keep the final score order; do not change generic/single-choice ranking.
    for pool in choice_ids:
        if len(selected) == 5:
            break
        if selected.isdisjoint(pool):
            best = next((id for id in ordered if id in pool), None)
            if best is not None:
                selected.add(best)
    for id in ordered:
        if len(selected) == 5:
            break
        selected.add(id)
    ids = [id for id in ordered if id in selected]
    return [
        {
            'id': id,
            'for_product_id': ranked[id][1],
            'reason': (
                f"{catalog.by_id[id].get('color','')} {catalog.by_id[id]['product_type']} "
                f"to accompany the selected {catalog.by_id[ranked[id][1]]['product_type']}."
            )[:300],
        }
        for id in ids
    ]
