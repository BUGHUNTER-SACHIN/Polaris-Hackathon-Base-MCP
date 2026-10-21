"""Conservative, deterministic shopping intent parsing. No generated product facts."""

from dataclasses import dataclass, field
import re


def normalize(text):
    text = text.casefold().replace("’", "'")
    text = re.sub(r"\b(women|men|girl|boy|kid|child|baby)'s\b", r"\1", text)
    return re.sub(r"\bt[ -]?shirts?\b", "tshirt", text)


def words(text):
    return tuple(re.findall(r"\w+", normalize(text)))


def parity_matches(product_id, parity):
    return parity is None or (
        re.fullmatch(r"[0-9]+", product_id) is not None
        and int(product_id) % 2 == parity
    )


# Reviewed aliases point to real catalog types; they are not product attributes.
TYPE_ALIASES = {
    "dress": ("Dress",),
    "dresses": ("Dress",),
    "top": ("Top", "Vest top"),
    "tshirt": ("T-shirt",),
    "tee": ("T-shirt",),
    "jeans": ("Trousers",),
    "trouser": ("Trousers",),
    "pants": ("Trousers",),
    "chinos": ("Trousers",),
    "jumper": ("Sweater",),
    "pullover": ("Sweater",),
    "sweatshirt": ("Sweater", "Hoodie"),
    "hoodie": ("Hoodie",),
    "trainer": ("Sneakers",),
    "sneaker": ("Sneakers",),
    "shoe": (
        "Sneakers",
        "Boots",
        "Sandals",
        "Other shoe",
        "Ballerinas",
        "Slippers",
        "Heeled sandals",
        "Pumps",
        "Flat shoe",
        "Flat shoes",
        "Heels",
        "Wedge",
        "Moccasins",
    ),
    "bag": (
        "Bag",
        "Shoulder bag",
        "Cross-body bag",
        "Tote bag",
        "Weekend/Gym bag",
        "Backpack",
        "Bumbag",
    ),
    "handbag": ("Bag", "Shoulder bag", "Cross-body bag", "Tote bag"),
    "purse": ("Bag", "Shoulder bag", "Cross-body bag"),
    "hat": (
        "Hat/beanie",
        "Hat/brim",
        "Beanie",
        "Felt hat",
        "Bucket hat",
        "Straw hat",
        "Cap/peaked",
        "Cap",
    ),
    "pyjama": ("Pyjama set", "Pyjama bottom", "Pyjama jumpsuit/playsuit", "Night gown"),
    "pajama": ("Pyjama set", "Pyjama bottom", "Pyjama jumpsuit/playsuit", "Night gown"),
    "legging": ("Leggings/Tights",),
    "tights": ("Leggings/Tights", "Underwear Tights"),
    "jumpsuit": ("Jumpsuit/Playsuit",),
    "playsuit": ("Jumpsuit/Playsuit",),
    "earring": ("Earring", "Earrings"),
    "swimwear": (
        "Swimsuit",
        "Swimwear top",
        "Swimwear bottom",
        "Swimwear set",
        "Bikini top",
    ),
    "bikini": ("Bikini top", "Swimwear bottom", "Swimwear set"),
}
for _type in (
    "Belt",
    "Shirt",
    "Skirt",
    "Sweater",
    "Jacket",
    "Coat",
    "Blouse",
    "Blazer",
    "Scarf",
    "Tie",
    "Necklace",
    "Bracelet",
    "Ring",
    "Wallet",
    "Sunglasses",
    "Backpack",
    "Cardigan",
    "Robe",
):
    TYPE_ALIASES.setdefault(_type.casefold(), (_type,))
TYPO_ALIASES = {
    "dres": "dress",
    "dresss": "dress",
    "sneekers": "sneakers",
    "snekaers": "sneakers",
    "tshrit": "tshirt",
    "trousres": "trousers",
    "sweatr": "sweater",
    "jakcet": "jacket",
    "jeen": "jeans",
}
COLOR_ALIASES = {
    "off-white": "off white",
    "navy-blue": "dark blue",
    "navy": "dark blue",
    "navy blue": "dark blue",
    "cream": "off white",
    "ivory": "off white",
    "gray": "grey",
    "burgundy": "dark red",
    "khaki": "greenish khaki",
}
PATTERN_ALIASES = {
    "polka-dot": "dot",
    "striped": "stripe",
    "stripes": "stripe",
    "checked": "check",
    "checkered": "check",
    "plaid": "check",
    "polka dot": "dot",
    "polka dots": "dot",
    "plain": "solid",
}
STOP = set(
    """a an the i me my we us our you your am is are be being want wants need
needs looking look search searching find show get buy buying shop shopping please
recommend suggest both either
some any something for of to in on at by from that this these those it its and or
with each per item items rupee rupees inr rs than only around about would like
can could should have has as wear wearing made product products option options""".split()
)
OCCASIONS = {
    "casual": ("cotton", "jersey", "canvas"),
    "formal": ("tailored", "satin", "suit", "lace"),
    "minimalist": ("solid",),
    "versatile": ("solid",),
    "dinner": ("satin", "velvet", "lace", "fitted"),
    "party": ("sequin", "glitter", "satin", "velvet"),
    "wedding": ("lace", "satin", "chiffon", "floral"),
    "office": ("tailored", "cotton", "collar", "blazer"),
    "work": ("tailored", "cotton", "collar"),
    "summer": ("linen", "cotton", "short", "sleeveless"),
    "winter": ("wool", "knit", "padded", "warm"),
    "beach": ("swim", "linen", "short"),
    "gym": ("sport", "training", "running"),
    "running": ("running", "sport"),
    "sunday": ("soft", "jersey", "cotton"),
    "lounge": ("soft", "jersey", "cotton"),
    "comfortable": ("soft", "jersey", "cotton"),
    "comfy": ("soft", "jersey", "cotton"),
}
AUDIENCE_WORDS = {
    "women": "women",
    "woman": "women",
    "womens": "women",
    "ladies": "women",
    "female": "women",
    "men": "men",
    "man": "men",
    "mens": "men",
    "male": "men",
    "girl": "girls",
    "girls": "girls",
    "boy": "boys",
    "boys": "boys",
    "kid": "children",
    "kids": "children",
    "child": "children",
    "children": "children",
    "baby": "baby",
    "babies": "baby",
}
COMPLEMENT = re.compile(
    r"\b(?:with\s+(?:(?:a|an|some)\s+)?(?:matching|complementary|coordinating|accompanying)"
    r"|(?:and\s+)?(?:a\s+)?(?:matching|complementary|accompanying)"
    r"|(?:paired|pair)\s+with)\b"
)
NUMBER = r"(?:\d[\d,]*(?:\.\d+)?\s*[kK]?)"
MONEY = r"(?:₹\s*|(?:inr|rs\.?|rupees?)\s*)?"
BUDGET = re.compile(
    rf"\b(?P<op>under|below|less than|no more than|no less than|"
    rf"within(?:\s+(?:a\s+)?budget(?:\s+of)?)?|budget(?:\s+of)?|"
    rf"up to|at most|maximum|max|over|above|at least|minimum|min)\s*"
    rf"{MONEY}(?P<value>{NUMBER})(?:\s*(?:inr|rupees?|rs\.?))?\b"
)
RANGE = re.compile(
    rf"\bbetween\s*{MONEY}(?P<low>{NUMBER})\s*and\s*{MONEY}(?P<high>{NUMBER})\b"
)

# Grammatical garment parts, not inferred product facts. A type modifying one of
# these nouns (e.g. 'shirt collar', 'jacket pockets') is lexical attribute evidence.
ATTRIBUTE_HEADS = (
    "collar", "collars", "sleeve", "sleeves", "neckline", "necklines",
    "pocket", "pockets", "hem", "hems", "cuff", "cuffs", "lining", "linings",
    "waistband", "waistbands", "print", "prints", "pattern", "patterns",
    "detail", "details",
    "fabric", "fabrics", "material", "materials", "blend", "blends",
    "weave", "weaves", "finish", "finishes", "trim", "trims",
    "hood", "hoods", "neck", "necks", "zip", "zips", "zipper", "zippers",
    "button", "buttons", "fastening", "fastenings", "slit", "slits",
    "embroidery", "design", "designs", "bow", "bows", "train", "trains",
)


def amount(text):
    return float(text.replace(",", "").replace(" ", "").rstrip("kK")) * (
        1000 if text.strip().lower().endswith("k") else 1
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
    quantity: int | None = None
    excluded_types: tuple = ()
    excluded_categories: tuple = ()
    nullable_rating: bool = False
    prefer_adult: bool = False
    phrases: tuple = ()


@dataclass
class QueryPlan:
    primary: list
    complements: list
    audience: str | None
    limit: int | None = None
    sort_by: str | None = None
    sort_order: str | None = None
    id_parity: int | None = None
    diverse: bool = False
    basket_budget: float | None = None
    unsupported_reason: str | None = None


def audience_matches(product, audience):
    """Source audience and section together disambiguate Sport and accessories."""
    if not audience:
        return True
    a, s = product.get("audience", "").casefold(), product.get("section", "").casefold()
    if audience == "men":
        return a == "menswear" or s.startswith(("men ", "mens ", "denim men"))
    if audience == "women":
        return a in (
            "ladieswear",
            "divided",
            "ladies accessories",
            "lingeries/tights",
        ) or s.startswith(("womens ", "ladies ", "mama"))
    if audience == "baby":
        return a.startswith("baby") or s.startswith("baby")
    if audience == "girls":
        return "girl" in s and not s.startswith("baby")
    if audience == "boys":
        return "boy" in s and not s.startswith("baby")
    return a.startswith("children") or s.startswith(("kids", "young", "girls", "boys"))


class QueryParser:
    def __init__(self, product_types, colors, patterns, categories=()):
        self.type_aliases = {
            normalize(t): (t,) for t in product_types if t != "Unknown"
        }
        self.type_aliases.update(TYPE_ALIASES)
        # Inflections of known names only, never arbitrary stemming of attributes.
        for key, values in list(self.type_aliases.items()):
            if not key.endswith("s"):
                self.type_aliases.setdefault(key + "s", values)
                if key.endswith("ss"):
                    self.type_aliases.setdefault(key + "es", values)
        self.colors = {normalize(c): c for c in colors if c not in ("Other", "Unknown")}
        self.patterns = {normalize(p): p for p in patterns if p != "Unknown"}
        self.categories = {normalize(c): c for c in categories}
        color_names = "(?:" + "|".join(
            re.escape(c) for c in sorted(
                set(self.colors) | set(COLOR_ALIASES), key=lambda s: (-len(s), s)
            )
        ) + ")"
        self.color_alternatives = re.compile(
            r"(?<!\w)" + color_names + r"(?:\s+or\s+" + color_names + r")+(?!\w)"
        )
        self.negative_colors = re.compile(
            r"\b(?:not|except|excluding|without|no|avoid)\s+" + color_names
            + r"(?:\s+(?:and|or)\s+" + color_names + r")+(?!\w)"
        )
        type_names = "|".join(
            re.escape(t) for t in sorted(self.type_aliases, key=lambda s: (-len(s), s))
        )
        self.attribute_phrase = re.compile(
            r"(?<!\w)(?:" + type_names + r")[\s-]+(?:"
            + "|".join(ATTRIBUTE_HEADS) + r")(?!\w)"
        )
        self.coordinated_attribute = re.compile(
            r"(?<!\w)" + color_names + r"(?:\s+and\s+" + color_names
            + r")+\s+(?:" + "|".join(ATTRIBUTE_HEADS) + r")(?!\w)"
        )

    def clause_boundaries(self, text, *, with_attributes=False):
        """Return connector spans without splitting units or color alternatives."""
        protected = [m.span() for m in RANGE.finditer(text)]
        protected += [m.span() for m in self.color_alternatives.finditer(text)]
        protected += [m.span() for m in self.negative_colors.finditer(text)]
        protected += [m.span() for m in re.finditer(
            r"\b\d(?:\.\d+)?\s*stars?\s+and\s+(?:above|over)\b", text
        )]
        connectors = r"and|or|plus|with" if with_attributes else r"and|or|plus"
        boundaries = []
        for match in re.finditer(
            r"\s+(?:" + connectors + r")\s+|\s*[,;]\s*(?!\d)", text
        ):
            token_start = match.start() + len(match.group()) - len(match.group().lstrip())
            if not any(a <= token_start < b for a, b in protected):
                boundaries.append(match)
        return boundaries

    def choice_clauses(self, text):
        boundaries = self.clause_boundaries(text)
        starts = [0] + [m.end() for m in boundaries]
        ends = [m.start() for m in boundaries] + [len(text)]
        return [text[a:b].strip(" .,") for a, b in zip(starts, ends)
                if text[a:b].strip(" .,")]

    def suffix_complement(self, text, audience):
        """Locate a requested item head; attributes before that head stay primary."""
        suffix = re.search(r"\s+(?:to match|to go with (?:it|them))\b", text)
        if not suffix:
            return [text]
        before = text[:suffix.start()]
        boundaries = self.clause_boundaries(before, with_attributes=True)
        candidates = []
        for index, separator in enumerate(boundaries):
            end = (boundaries[index + 1].start()
                   if index + 1 < len(boundaries) else len(before))
            head = before[separator.end():end].strip()
            intent = self.parse_intent(head, audience)
            # Attribute nouns are not requested items, even when modified by a
            # catalog type. An indefinite noun phrase can name an unsupported
            # item; its availability is evaluated only after scope is established.
            attribute_only = not intent.types and (
                intent.phrases or set(words(head)).intersection(ATTRIBUTE_HEADS)
            )
            # An article plus a color alone is a modifier fragment, not an item
            # head: the following conjunction may still precede 'white print'.
            item_head = intent.types or (
                intent.terms and re.match(r"^(?:a|an)\s+\w", head)
            )
            if item_head and not attribute_only:
                candidates.append(separator)
        if candidates:
            # Explicit attachment binds after earlier mixed primary choices.
            # E.g. 'dress plus skirt with a bag' keeps both clothing choices.
            separator = next((m for m in candidates if m.group().strip() == "with"),
                             candidates[0])
            return [before[:separator.start()],
                    before[separator.end():] + text[suffix.end():]]
        return [text]

    @staticmethod
    def _extract(text, phrases):
        found = []
        for phrase in sorted(phrases, key=lambda s: (-len(s), s)):
            pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
            if re.search(pattern, text):
                found.append(phrases[phrase])
                text = re.sub(pattern, " ", text)
        return text, found

    def budgets(self, text):
        filters = {}

        def span(match):
            filters["min_price"] = amount(match["low"])
            filters["max_price"] = amount(match["high"])
            return " "

        text = RANGE.sub(span, text)

        def bound(match):
            key = (
                "min_price"
                if match["op"]
                in ("over", "above", "at least", "minimum", "min", "no less than")
                else "max_price"
            )
            value = amount(match["value"])
            filters[key] = (min if key == "max_price" else max)(
                filters.get(key, value), value
            )
            return " "

        # Ratings/reviews are removed before money parsing in parse_intent.
        return BUDGET.sub(bound, text), filters

    @staticmethod
    def controls(text):
        """Consume result controls before item numbers can be interpreted as money."""
        controls = {}

        def count(match):
            value = int(match[1])
            controls["limit"] = min(controls.get("limit", value), value)
            return " "

        text = re.sub(
            r"\b(?:(?:show|return|give me)\s+)?(?:at most|up to|maximum|max|no more than)\s+"
            r"(\d+)\s+(?:results?|products?|options?)\b",
            count,
            text,
        )

        def ordering(match):
            controls["sort_by"] = "price"
            controls["sort_order"] = "asc" if match[1] == "ascending" else "desc"
            return " "

        text = re.sub(r"\bsort by price\s+(ascending|descending)\b", ordering, text)
        for phrase, direction in (
            ("cheapest first", "asc"),
            ("most expensive first", "desc"),
        ):
            if phrase in text:
                controls.update(sort_by="price", sort_order=direction)
                text = text.replace(phrase, " ")
        return text, controls

    def parse_intent(self, text, audience):
        text = normalize(text)
        text = self.color_alternatives.sub(
            lambda m: re.sub(r"\s+or\s+", " / ", m.group()), text
        )
        unsupported = bool(re.search(
            r"\b(?:size\s*(?:xxxs|xxs|xs|s|m|l|xl|xxl|xxxl|\d{1,2}(?:xl)?)"
            r"|in stock|out of stock|inventory|next day delivery|delivery tomorrow"
            r"|free shipping|discount(?:ed)?|on sale)\b",
            text,
        ))
        audience = next(
            (AUDIENCE_WORDS[w] for w in words(text) if w in AUDIENCE_WORDS), audience
        )
        text = " ".join(
            TYPO_ALIASES.get(w, w) for w in re.findall(r"\w+|[^\w\s]", text)
        )
        # Repair punctuation spacing from token substitution before phrase extraction.
        text = re.sub(r"\s*([,/.-])\s*", r"\1", text)
        filters = {}
        quantity = None
        nullable_rating = bool(
            re.search(r"\bif ratings? (?:are |is )?available\b", text)
        )
        text = re.sub(r"\bif ratings? (?:are |is )?available\b", " ", text)

        def rating(match):
            value = float(match[1])
            filters["min_rating"] = max(filters.get("min_rating", value), value)
            return " "

        def reviews(match):
            value = int(match[1].replace(",", ""))
            filters["min_review_count"] = max(
                filters.get("min_review_count", value), value
            )
            return " "

        # Explicit star units are consumed before monetary bounds and quantities.
        text = re.sub(
            r"\b(\d(?:\.\d+)?)\s*(?:\+\s*stars?\b|stars?\s+(?:and\s+)?(?:above|over)\b)",
            rating,
            text,
        )
        # A preceding 'rated' is grammar after the unit-bearing clause is removed.
        text = re.sub(r"\brated\s+(?=\s|$)", " ", text)
        text = re.sub(
            r"\b(?:rated\s+(?:at least\s+)?|(?:a\s+)?rating\s+(?:of\s+)?(?:at least|min(?:imum)?)\s+)"
            r"(\d(?:\.\d+)?)(?:\s*(?:stars?|rating))?\b",
            rating,
            text,
        )
        text = re.sub(
            r"\b(?:at least|min(?:imum)?(?: rating)?|rated)\s+(\d(?:\.\d+)?)\s*(?:stars?|rating)\b",
            rating,
            text,
        )
        text = re.sub(
            r"\b(?:at least|min(?:imum)?)\s+(\d[\d,]*)\s+reviews?\b", reviews, text
        )
        quantity_match = re.match(
            r"^\s*(?:(?:find|show|get)\s+)?(?:(?:at least|at most|exactly)\s+)?"
            r"(\d+)\s+(?=\w)",
            text,
        )
        if quantity_match:
            quantity = int(quantity_match[1])
            text = text[quantity_match.end() :]
        text, money = self.budgets(text)
        filters.update(money)
        excluded_colors, excluded_terms, excluded_types, excluded_categories = (
            [],
            [],
            [],
            [],
        )

        def exclude_term(term):
            color = COLOR_ALIASES.get(term, term)
            if color in self.colors:
                excluded_colors.extend(self._color_family(color))
            elif term in self.type_aliases:
                excluded_types.extend(self.type_aliases[term])
            elif term in self.categories:
                excluded_categories.append(self.categories[term])
            else:
                excluded_terms.extend(words(term))
            return " "

        # Match a complete known phrase before the fallback single lexical term.
        exclusions = sorted(
            set(self.colors)
            | set(COLOR_ALIASES)
            | set(self.type_aliases)
            | set(self.categories),
            key=lambda s: (-len(s), s),
        )
        alternatives = "|".join(re.escape(p) for p in exclusions)

        def exclude(match):
            # The known-phrase matcher consumes slash-bearing type names whole.
            for term in re.findall("(?:" + alternatives + r")(?!\w)|\w+", match[1]):
                if term not in ("or", "and"):
                    exclude_term(term)
            return " "

        phrase = "(?:" + alternatives + r"|\w+)(?!\w)"
        text = re.sub(
            r"\b(?:not|except|excluding|without|no|avoid)\s+("
            + phrase
            + r"(?:\s*(?:/|\bor\b|\band\b)\s*"
            + phrase
            + ")*)",
            exclude,
            text,
        )
        phrases = []

        def attribute(match):
            phrases.append(" ".join(words(match.group())))
            return " "

        # A coordinated modifier on a garment part is a source requirement,
        # not an OR over whole-product color facets. Retain its complete phrase.
        text = self.coordinated_attribute.sub(attribute, text)
        strict_colors = "/" in text
        neutral = bool(re.search(r"\bneutral(?:-colou?red| colou?red)?\b", text))
        text = re.sub(r"\bneutral(?:-colou?red| colou?red)?\b", " ", text)
        # Color aliases are replaced before longest-first exact catalog matching.
        for alias in sorted(COLOR_ALIASES, key=len, reverse=True):
            text = re.sub(r"\b" + re.escape(alias) + r"\b", COLOR_ALIASES[alias], text)
        text, color_values = self._extract(text, self.colors)
        colors = []
        for c in color_values:
            colors.extend((c,) if strict_colors else self._color_family(normalize(c)))
        if neutral:
            colors.extend(
                c
                for c in self.colors.values()
                if c
                in (
                    "Black",
                    "White",
                    "Off White",
                    "Beige",
                    "Light Beige",
                    "Dark Beige",
                    "Greyish Beige",
                    "Grey",
                    "Light Grey",
                    "Dark Grey",
                )
            )
        for alias in sorted(PATTERN_ALIASES, key=len, reverse=True):
            text = re.sub(
                r"\b" + re.escape(alias) + r"\b", PATTERN_ALIASES[alias], text
            )
        text, pattern_values = self._extract(text, self.patterns)
        text = self.attribute_phrase.sub(attribute, text)
        # Jeans are a trouser subtype and must still have lexical denim/jeans evidence.
        subtype = next(
            (t for t in ("jeans", "chinos") if re.search(r"\b" + t + r"\b", text)), None
        )
        text, type_values = self._extract(text, self.type_aliases)
        types = tuple(dict.fromkeys(t for group in type_values for t in group))
        soft, residual = [], []
        for word in words(text):
            if word in OCCASIONS:
                soft.extend(OCCASIONS[word])
            elif (
                word not in STOP
                and word not in AUDIENCE_WORDS
                and word not in ("lazy",)
            ):
                residual.append(word)
        if subtype:
            residual.append(subtype)
        for phrase in phrases:
            residual.extend(words(phrase))
        if not types and soft:
            if any(w in words(text) for w in ("sunday", "comfortable", "comfy", "lounge")):
                types = (
                    "Hoodie",
                    "Sweater",
                    "Pyjama set",
                    "Pyjama bottom",
                    "Robe",
                    "Slippers",
                    "T-shirt",
                )
            elif any(w in words(text) for w in ("gym", "running")):
                types = ("Leggings/Tights", "Shorts", "T-shirt", "Sneakers")
            elif any(w in words(text) for w in ("office", "work")):
                types = ("Blazer", "Shirt", "Trousers", "Blouse")
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
            quantity=quantity,
            excluded_types=tuple(dict.fromkeys(excluded_types)),
            excluded_categories=tuple(dict.fromkeys(excluded_categories)),
            nullable_rating=nullable_rating,
            unsupported=unsupported,
            phrases=tuple(dict.fromkeys(phrases)),
        )

    def _color_family(self, color):
        # Unqualified blue includes Dark Blue; explicit filters remain exact.
        if " " not in color:
            return tuple(
                v
                for k, v in self.colors.items()
                if k == color or k.endswith(" " + color)
            )
        return (self.colors[color],) if color in self.colors else ()

    def choices(self, text, audience, *, complementary=False):
        shared = {}

        def shared_money(match):
            nonlocal shared
            _, shared = self.budgets(match[1])
            return " "

        text = re.sub(
            r",?\s*\ball\s+(" + BUDGET.pattern + r")(?:\s+per item)?",
            shared_money,
            text,
        )
        clauses = self.choice_clauses(text)
        intents = [
            self.parse_intent(re.sub(r"^(?:and|or)\s+", "", c.strip(" .,")), audience)
            for c in clauses
            if c.strip(" .,")
        ]
        if not intents:
            intents = [self.parse_intent("", audience)]
        if not complementary and len(intents) > 1 and not all(i.types for i in intents):
            intents = [self.parse_intent(text, audience)]
        if complementary:
            negatives = [i for i in intents if not (i.types or i.terms or i.filters
                         or i.colors or i.patterns) and any((i.excluded_colors,
                         i.excluded_types, i.excluded_terms, i.excluded_categories))]
            intents = [i for i in intents if i not in negatives]
            for intent in intents:
                for field in ("excluded_colors", "excluded_types", "excluded_terms",
                              "excluded_categories"):
                    setattr(intent, field, tuple(dict.fromkeys(
                        getattr(intent, field) + tuple(
                            value for negative in negatives
                            for value in getattr(negative, field)
                        )
                    )))
                # A generic accessory is supported, but a laptop word in a bag's
                # description cannot make that bag the requested laptop.
                if not intent.types and intent.terms:
                    if intent.terms in (("accessory",), ("accessories",)):
                        intent.terms = ()
                    else:
                        intent.unsupported = True
            if not intents:
                intents = [Intent(meaningful=True, unsupported=True)]
        if len(intents) > 1:
            # Share a sole trailing constraint after it has been assigned its unit.
            # Rescanning raw text here would turn rating/review numbers into prices.
            for keys in (
                ("min_price", "max_price"),
                ("min_rating",),
                ("min_review_count",),
            ):
                if not any(any(k in i.filters for k in keys) for i in intents[:-1]):
                    for intent in intents[:-1]:
                        for key in keys:
                            if key in intents[-1].filters:
                                intent.filters[key] = intents[-1].filters[key]
                    if "min_rating" in keys:
                        for intent in intents[:-1]:
                            intent.nullable_rating = intents[-1].nullable_rating
        for intent in intents:
            for k, v in shared.items():
                intent.filters.setdefault(k, v)
        return intents

    def parse(self, query):
        text = normalize(query)
        # Strip a request prefix, never a product's residual 'love' attribute.
        text = re.sub(r"^\s*(?:i|we)(?:\s+would|'d)\s+love\s+", "", text)
        text, controls = self.controls(text)
        # Combined budgets and already-owned inventory have no representation in v1.
        basket = re.search(
            r"\b(?:total|combined|basket)\s+(?:cost|budget|price)?\s*"
            r"(?:under|below|of)\s*" + MONEY + "(" + NUMBER + ")",
            text,
        )
        if basket or re.search(r"\bi\s+(?:bought|own|already have)\b", text):
            return QueryPlan(
                [Intent(unsupported=True)],
                [],
                None,
                basket_budget=amount(basket[1]) if basket else None,
                unsupported_reason="basket budget" if basket else "owned-item context",
            )

        parity = None

        def parity_clause(match):
            nonlocal parity
            parity = 0 if match[1] == "even" else 1
            return " "

        text = re.sub(
            r"\b(?:return only\s+)?products whose (?:numeric\s+)?product ids are (even|odd)\b",
            parity_clause,
            text,
        )
        text = re.sub(
            r"\b(?:with\s+)?(even|odd)[ -]numbered product ids\b", parity_clause, text
        )
        diverse = bool(re.search(r"\b(?:varied|diverse)\b", text))
        prefer_adult = bool(re.search(r"\bcollege\b", text))
        minimalist = bool(re.search(r"\bminimalist\b", text))
        text = re.sub(
            r"\b(?:give me|show|return)\s+(?:a\s+)?(?:varied|diverse)\s+(?:set of\s+)?options"
            r"(?:\s+rather than\s+\w+\s+(?:nearly\s+)?identical products)?",
            " ",
            text,
        )
        # Reviewed non-product context; unknown attributes elsewhere stay hard terms.
        text = re.sub(
            r"\bi(?: am|'m)\s+(?:building|creating|updating)\s+(?:a\s+)?"
            r"(?:minimalist\s+)?wardrobe(?:\s+for college)?\s*[.]?",
            " ",
            text,
        )
        audiences = {AUDIENCE_WORDS[w] for w in words(text) if w in AUDIENCE_WORDS}
        audience = next(iter(audiences)) if len(audiences) == 1 else None
        parts = COMPLEMENT.split(text, maxsplit=1)
        if len(parts) == 1:
            parts = self.suffix_complement(text, audience)
        intents = self.choices(parts[0], audience)
        complements = (self.choices(parts[1], audience, complementary=True)
                       if len(parts) > 1 else [])
        for intent in intents:
            intent.prefer_adult = prefer_adult
            if minimalist:
                intent.soft = tuple(sorted(set(intent.soft) | {"solid"}))
        if complements:
            for complement in complements:
                if not any(k in complement.filters for k in ("min_price", "max_price")):
                    complement.filters.update(
                        {
                            k: v
                            for k, v in intents[0].filters.items()
                            if k in ("min_price", "max_price")
                        }
                    )
        if all(i.quantity is not None for i in intents) and "limit" not in controls:
            controls["limit"] = sum(i.quantity for i in intents)
        return QueryPlan(
            intents,
            complements,
            audience,
            id_parity=parity,
            diverse=diverse,
            **controls,
        )
