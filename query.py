"""Conservative, deterministic shopping intent parsing. No generated product facts."""

from dataclasses import dataclass, field
import re


def normalize(text):
    text = text.casefold().replace('’', "'")
    text = re.sub(r"\b(women|men|girl|boy|kid|child|baby)'s\b", r'\1', text)
    return re.sub(r'\bt[ -]?shirts?\b', 'tshirt', text)


def words(text):
    return tuple(re.findall(r'\w+', normalize(text)))


# Reviewed aliases point to real catalog types; they are not product attributes.
TYPE_ALIASES = {
    'dress': ('Dress',),
    'dresses': ('Dress',),
    'top': ('Top', 'Vest top'),
    'tshirt': ('T-shirt',),
    'tee': ('T-shirt',),
    'jeans': ('Trousers',),
    'trouser': ('Trousers',),
    'pants': ('Trousers',),
    'jumper': ('Sweater',),
    'pullover': ('Sweater',),
    'sweatshirt': ('Sweater', 'Hoodie'),
    'hoodie': ('Hoodie',),
    'trainer': ('Sneakers',),
    'sneaker': ('Sneakers',),
    'shoe': (
        'Sneakers',
        'Boots',
        'Sandals',
        'Other shoe',
        'Ballerinas',
        'Slippers',
        'Heeled sandals',
        'Pumps',
        'Flat shoe',
        'Flat shoes',
        'Heels',
        'Wedge',
        'Moccasins',
    ),
    'bag': (
        'Bag',
        'Shoulder bag',
        'Cross-body bag',
        'Tote bag',
        'Weekend/Gym bag',
        'Backpack',
        'Bumbag',
    ),
    'handbag': ('Bag', 'Shoulder bag', 'Cross-body bag', 'Tote bag'),
    'purse': ('Bag', 'Shoulder bag', 'Cross-body bag'),
    'hat': (
        'Hat/beanie',
        'Hat/brim',
        'Beanie',
        'Felt hat',
        'Bucket hat',
        'Straw hat',
        'Cap/peaked',
        'Cap',
    ),
    'pyjama': ('Pyjama set', 'Pyjama bottom', 'Pyjama jumpsuit/playsuit', 'Night gown'),
    'pajama': ('Pyjama set', 'Pyjama bottom', 'Pyjama jumpsuit/playsuit', 'Night gown'),
    'legging': ('Leggings/Tights',),
    'tights': ('Leggings/Tights', 'Underwear Tights'),
    'jumpsuit': ('Jumpsuit/Playsuit',),
    'playsuit': ('Jumpsuit/Playsuit',),
    'earring': ('Earring', 'Earrings'),
    'swimwear': (
        'Swimsuit',
        'Swimwear top',
        'Swimwear bottom',
        'Swimwear set',
        'Bikini top',
    ),
    'bikini': ('Bikini top', 'Swimwear bottom', 'Swimwear set'),
}
for _type in (
    'Belt',
    'Shirt',
    'Skirt',
    'Sweater',
    'Jacket',
    'Coat',
    'Blouse',
    'Blazer',
    'Scarf',
    'Tie',
    'Necklace',
    'Bracelet',
    'Ring',
    'Wallet',
    'Sunglasses',
    'Backpack',
    'Cardigan',
    'Robe',
):
    TYPE_ALIASES.setdefault(_type.casefold(), (_type,))
TYPO_ALIASES = {
    'dres': 'dress',
    'dresss': 'dress',
    'sneekers': 'sneakers',
    'snekaers': 'sneakers',
    'tshrit': 'tshirt',
    'trousres': 'trousers',
    'sweatr': 'sweater',
    'jakcet': 'jacket',
    'jeen': 'jeans',
}
COLOR_ALIASES = {
    'navy': 'dark blue',
    'navy blue': 'dark blue',
    'cream': 'off white',
    'ivory': 'off white',
    'gray': 'grey',
    'burgundy': 'dark red',
    'khaki': 'greenish khaki',
}
PATTERN_ALIASES = {
    'striped': 'stripe',
    'stripes': 'stripe',
    'checked': 'check',
    'checkered': 'check',
    'plaid': 'check',
    'polka dot': 'dot',
    'polka dots': 'dot',
    'plain': 'solid',
}
STOP = set(
    '''a an the i me my we us our you your am is are be being want wants need
needs looking look search searching find show get buy buying shop shopping please
some any something for of to in on at by from that this these those it its and or
with each per item items rupee rupees inr rs than only around about would like
can could should have has as wear wearing made product products option options'''.split()
)
OCCASIONS = {
    'dinner': ('satin', 'velvet', 'lace', 'fitted'),
    'party': ('sequin', 'glitter', 'satin', 'velvet'),
    'wedding': ('lace', 'satin', 'chiffon', 'floral'),
    'office': ('tailored', 'cotton', 'collar', 'blazer'),
    'work': ('tailored', 'cotton', 'collar'),
    'summer': ('linen', 'cotton', 'short', 'sleeveless'),
    'winter': ('wool', 'knit', 'padded', 'warm'),
    'beach': ('swim', 'linen', 'short'),
    'gym': ('sport', 'training', 'running'),
    'running': ('running', 'sport'),
    'sunday': ('soft', 'jersey', 'cotton'),
    'lounge': ('soft', 'jersey', 'cotton'),
    'comfortable': ('soft', 'jersey', 'cotton'),
}
AUDIENCE_WORDS = {
    'women': 'women',
    'woman': 'women',
    'womens': 'women',
    'ladies': 'women',
    'female': 'women',
    'men': 'men',
    'man': 'men',
    'mens': 'men',
    'male': 'men',
    'girl': 'girls',
    'girls': 'girls',
    'boy': 'boys',
    'boys': 'boys',
    'kid': 'children',
    'kids': 'children',
    'child': 'children',
    'children': 'children',
    'baby': 'baby',
    'babies': 'baby',
}
COMPLEMENT = re.compile(
    r'\b(?:with\s+(?:(?:a|an|some)\s+)?(?:matching|complementary|coordinating|accompanying)'
    r'|(?:and\s+)?(?:a\s+)?(?:matching|complementary|accompanying)'
    r'|(?:paired|pair)\s+with)\b'
)
NUMBER = r'(?:\d[\d,]*(?:\.\d+)?\s*[kK]?)'
MONEY = r'(?:₹\s*|(?:inr|rs\.?|rupees?)\s*)?'
BUDGET = re.compile(
    rf'\b(?P<op>under|below|less than|up to|at most|maximum|max|over|above|at least|minimum|min)\s*'
    rf'{MONEY}(?P<value>{NUMBER})(?:\s*(?:inr|rupees?|rs\.?))?\b'
)
RANGE = re.compile(
    rf'\bbetween\s*{MONEY}(?P<low>{NUMBER})\s*and\s*{MONEY}(?P<high>{NUMBER})\b'
)


def amount(text):
    return float(text.replace(',', '').replace(' ', '').rstrip('kK')) * (
        1000 if text.strip().lower().endswith('k') else 1
    )


@dataclass
class Intent:
    terms: tuple = ()
    types: tuple = ()
    colors: tuple = ()
    patterns: tuple = ()
    filters: dict = field(default_factory=dict)
    excluded_colors: tuple = ()
    excluded_terms: tuple = ()
    soft: tuple = ()
    audience: str | None = None
    meaningful: bool = False
    unsupported: bool = False


@dataclass
class QueryPlan:
    primary: list
    complements: list
    audience: str | None


def audience_matches(product, audience):
    """Source audience and section together disambiguate Sport and accessories."""
    if not audience:
        return True
    a, s = product.get('audience', '').casefold(), product.get('section', '').casefold()
    if audience == 'men':
        return a == 'menswear' or s.startswith(('men ', 'mens ', 'denim men'))
    if audience == 'women':
        return a in (
            'ladieswear',
            'divided',
            'ladies accessories',
            'lingeries/tights',
        ) or s.startswith(('womens ', 'ladies ', 'mama'))
    if audience == 'baby':
        return a.startswith('baby') or s.startswith('baby')
    if audience == 'girls':
        return 'girl' in s and not s.startswith('baby')
    if audience == 'boys':
        return 'boy' in s and not s.startswith('baby')
    return a.startswith('children') or s.startswith(('kids', 'young', 'girls', 'boys'))


class QueryParser:
    def __init__(self, product_types, colors, patterns):
        self.type_aliases = {
            normalize(t): (t,) for t in product_types if t != 'Unknown'
        }
        self.type_aliases.update(TYPE_ALIASES)
        # Inflections of known names only, never arbitrary stemming of attributes.
        for key, values in list(self.type_aliases.items()):
            if not key.endswith('s'):
                self.type_aliases.setdefault(key + 's', values)
                if key.endswith('ss'):
                    self.type_aliases.setdefault(key + 'es', values)
        self.colors = {normalize(c): c for c in colors if c not in ('Other', 'Unknown')}
        self.patterns = {normalize(p): p for p in patterns if p != 'Unknown'}

    @staticmethod
    def _extract(text, phrases):
        found = []
        for phrase in sorted(phrases, key=lambda s: (-len(s), s)):
            pattern = r'(?<!\w)' + re.escape(phrase) + r'(?!\w)'
            if re.search(pattern, text):
                found.append(phrases[phrase])
                text = re.sub(pattern, ' ', text)
        return text, found

    def budgets(self, text):
        filters = {}

        def span(match):
            filters['min_price'] = amount(match['low'])
            filters['max_price'] = amount(match['high'])
            return ' '

        text = RANGE.sub(span, text)

        def bound(match):
            key = (
                'min_price'
                if match['op'] in ('over', 'above', 'at least', 'minimum', 'min')
                else 'max_price'
            )
            value = amount(match['value'])
            filters[key] = (min if key == 'max_price' else max)(
                filters.get(key, value), value
            )
            return ' '

        # Ratings/reviews are removed before money parsing in parse_intent.
        return BUDGET.sub(bound, text), filters

    def parse_intent(self, text, audience):
        text = normalize(text)
        if re.search(
            r'\b(?:size\s*(?:xxxs|xxs|xs|s|m|l|xl|xxl|xxxl|\d{1,2}(?:xl)?)'
            r'|in stock|out of stock|inventory|next day delivery|delivery tomorrow'
            r'|free shipping|discount(?:ed)?|on sale)\b',
            text,
        ):
            # The catalog has no garment-size availability, stock, shipping or discount facts.
            return Intent(audience=audience, meaningful=True, unsupported=True)
        audience = next(
            (AUDIENCE_WORDS[w] for w in words(text) if w in AUDIENCE_WORDS), audience
        )
        text = ' '.join(
            TYPO_ALIASES.get(w, w) for w in re.findall(r'\w+|[^\w\s]', text)
        )
        # Repair punctuation spacing from token substitution before phrase extraction.
        text = re.sub(r'\s*([,/.-])\s*', r'\1', text)
        filters = {}

        def rating(match):
            filters['min_rating'] = float(match[1])
            return ' '

        def reviews(match):
            filters['min_review_count'] = int(match[1])
            return ' '

        text = re.sub(
            r'\b(?:at least|min(?:imum)?(?: rating)?|rated)\s+(\d(?:\.\d+)?)\s*(?:stars?|rating)\b',
            rating,
            text,
        )
        text = re.sub(
            r'\b(?:at least|min(?:imum)?)\s+(\d+)\s+reviews?\b', reviews, text
        )
        text, money = self.budgets(text)
        filters.update(money)
        excluded_colors, excluded_terms = [], []

        def exclude(match):
            term = match[1]
            color = COLOR_ALIASES.get(term, term)
            if color in self.colors:
                excluded_colors.extend(self._color_family(color))
            else:
                excluded_terms.extend(words(term))
            return ' '

        text = re.sub(
            r'\b(?:not|except|excluding|without|no)\s+([\w]+)\b', exclude, text
        )
        # Color aliases are replaced before longest-first exact catalog matching.
        for alias in sorted(COLOR_ALIASES, key=len, reverse=True):
            text = re.sub(r'\b' + re.escape(alias) + r'\b', COLOR_ALIASES[alias], text)
        text, color_values = self._extract(text, self.colors)
        colors = []
        for c in color_values:
            colors.extend(self._color_family(normalize(c)))
        for alias in sorted(PATTERN_ALIASES, key=len, reverse=True):
            text = re.sub(
                r'\b' + re.escape(alias) + r'\b', PATTERN_ALIASES[alias], text
            )
        text, pattern_values = self._extract(text, self.patterns)
        # Jeans are a trouser subtype and must still have lexical denim/jeans evidence.
        jeans = bool(re.search(r'\bjeans\b', text))
        text, type_values = self._extract(text, self.type_aliases)
        types = tuple(dict.fromkeys(t for group in type_values for t in group))
        soft, residual = [], []
        for word in words(text):
            if word in OCCASIONS:
                soft.extend(OCCASIONS[word])
            elif (
                word not in STOP
                and word not in AUDIENCE_WORDS
                and word not in ('lazy',)
            ):
                residual.append(word)
        if jeans:
            residual.append('jeans')
        if not types and soft:
            if any(w in words(text) for w in ('sunday', 'comfortable', 'lounge')):
                types = (
                    'Hoodie',
                    'Sweater',
                    'Pyjama set',
                    'Pyjama bottom',
                    'Robe',
                    'Slippers',
                    'T-shirt',
                )
            elif any(w in words(text) for w in ('gym', 'running')):
                types = ('Leggings/Tights', 'Shorts', 'T-shirt', 'Sneakers')
            elif any(w in words(text) for w in ('office', 'work')):
                types = ('Blazer', 'Shirt', 'Trousers', 'Blouse')
        return Intent(
            tuple(residual),
            types,
            tuple(dict.fromkeys(colors)),
            tuple(pattern_values),
            filters,
            tuple(excluded_colors),
            tuple(excluded_terms),
            tuple(sorted(set(soft))),
            audience,
            bool(residual or types or colors or pattern_values or filters or audience),
        )

    def _color_family(self, color):
        # Unqualified blue includes Dark Blue; explicit filters remain exact.
        if ' ' not in color:
            return tuple(
                v
                for k, v in self.colors.items()
                if k == color or k.endswith(' ' + color)
            )
        return (self.colors[color],) if color in self.colors else ()

    def choices(self, text, audience):
        # Do not split the 'and' inside a price range.
        primary_text = RANGE.sub(lambda m: m.group().replace(' and ', ' to '), text)
        clauses = re.split(r'\s+(?:and|or)\s+|\s*[,;]\s*(?!\d)', primary_text)
        clauses = [
            re.sub(r'\bbetween\s+(.+?)\s+to\s+', r'between \1 and ', c) for c in clauses
        ]
        intents = [self.parse_intent(c, audience) for c in clauses]
        if len(intents) > 1 and not all(i.types for i in intents):
            intents = [self.parse_intent(text, audience)]
        if len(intents) > 1:
            _, budgets = self.budgets(text)
            # A single budget at the end is shared, per item; multiple budgets stay scoped.
            if len(BUDGET.findall(text)) == 1 and intents[-1].filters:
                for intent in intents:
                    for k, v in budgets.items():
                        intent.filters.setdefault(k, v)
        return intents

    def parse(self, query):
        text = normalize(query)
        audiences = {AUDIENCE_WORDS[w] for w in words(text) if w in AUDIENCE_WORDS}
        audience = next(iter(audiences)) if len(audiences) == 1 else None
        parts = COMPLEMENT.split(text, maxsplit=1)
        intents = self.choices(parts[0], audience)
        complements = self.choices(parts[1], audience) if len(parts) > 1 else []
        if complements:
            for complement in complements:
                if not any(k in complement.filters for k in ('min_price', 'max_price')):
                    complement.filters.update(
                        {
                            k: v
                            for k, v in intents[0].filters.items()
                            if k in ('min_price', 'max_price')
                        }
                    )
        return QueryPlan(intents, complements, audience)
