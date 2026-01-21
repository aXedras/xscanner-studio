"""Producer synonym mappings and normalization utilities for strategy comparison."""

import re


def canonicalize_producer_key(value: str) -> str:
    """Normalize producer strings for fuzzy comparisons."""
    cleaned = re.sub(r"[^a-z0-9]", " ", value.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


RAW_PRODUCER_SYNONYMS = {
    # Swiss refiners
    "argor heraeus": {
        "argor heraeus",
        "argor-heraeus",
        "argor",
        "argor sa",
        "argor group",
        "argor heraeus sa",
        "argor-heraeus sa",
        "argor-heraeus s.a.",
        "argor heraeus s.a.",
        "argor heraeus s a",
        "argor heraeus sa switzerland",
        "argor-heraeus sa switzerland",
        "argor heraeus s.a. switzerland",
        "argor heraeus switzerland",
    },
    "heraeus": {
        "heraeus",
        "heraeus sa",
        "heraeus gmbh",
        "heraeus ag",
        "heraeus feinsilber",
        "heraeus feingold",
        "heræus",  # OCR may read the ligature
    },
    "valcambi": {
        "valcambi",
        "valcambi sa",
        "valcambi suisse",
        "valcambi s.a.",
        "valcambi suisse sa",
        "chi essayeur fondeur",
        "chi fondeur",
        "chi",  # Valcambi hallmark on platinum bars
    },
    "umicore": {
        "umicore",
        "umicore sa",
        "umicore ag",
        "umicore feinsilber",
        "umicore precious metals",
    },
    "mks pamp": {
        "mks pamp",
        "pamp",
        "mks",
        "pamp suisse",
        "pamp sa",
        "pamp s.a.",
        "pamp switzerland",
        "mks pamp sa",
    },
    "metalor": {"metalor", "metalor technologies", "metalor sa"},
    # Swiss banks
    "credit suisse": {
        "credit suisse",
        "cs",
        "credit-suisse",
        "crédit suisse",
        "credit suisse gold",
        "credit suisse sa",
    },
    "ubs": {"ubs", "ubs ag", "ubs switzerland"},
    "clariden leu": {"clariden leu", "clariden", "clariden leu ag"},
    "raiffeisen": {"raiffeisen", "raiffeisenbank"},
    "commerzbank": {"commerzbank", "commerzbank ag"},
    "degussa": {"degussa", "degussas", "degussa goldhandel"},
    "kantonalbank": {"kantonalbank", "kantonal bank"},
    "metaux precieux": {
        "metaux precieux",
        "metaux precieux s.a.",
        "metaux precieux sa",
        "métaux précieux",
        "métaux précieux sa",
    },
    # International mints/refiners
    "perth mint": {"perth mint", "the perth mint", "perth mint australia"},
    "rcm": {"rcm", "royal canadian mint", "royal canadian mint rcm"},
    "rmc": {"rmc", "republic metals", "republic metals corporation"},
    "asahi": {"asahi", "asahi refining", "asahi refinery", "asahi refining usa", "asah"},
    # Additional producers from test data
    "swiss bank corporation": {"swiss bank corporation", "sbc"},
    "rand refinery": {"rand refinery", "rand refinery south africa"},
    "johnson matthey": {"johnson matthey", "jm", "johnson matthey london"},
    "engelhard": {"engelhard", "engelhard industries"},
}

PRODUCER_SYNONYM_MAP: dict[str, set[str]] = {
    canonical: {
        canonicalize_producer_key(alias)
        for alias in ({canonical} | aliases)
        if canonicalize_producer_key(alias)
    }
    for canonical, aliases in RAW_PRODUCER_SYNONYMS.items()
}


def normalize_producer(value: str | None) -> str | None:
    """Normalize producer name using synonym mapping.

    Uses multiple matching strategies:
    1. Exact match against known synonyms
    2. Substring match (e.g., "ARGOR-HERAEUS S.A. Switzerland" → "argor heraeus")
    3. Contains canonical name (e.g., "Umicore Feinsilber 999" → "umicore")
    4. Fuzzy match for common OCR typos

    Args:
        value: Producer name to normalize

    Returns:
        Normalized canonical producer name or None
    """
    if value is None:
        return None
    text = re.sub(r"\([^)]*\)", "", str(value))
    normalized = canonicalize_producer_key(text)
    if not normalized:
        return None

    # Blacklist: words that are too generic and should not match alone
    generic_words = {"switzerland", "germany", "usa", "australia", "london", "sa", "ag", "gmbh"}
    if normalized in generic_words:
        return None

    # Strategy 1: Exact match against known synonyms
    for canonical, variants in PRODUCER_SYNONYM_MAP.items():
        if normalized in variants:
            return canonical

    # Strategy 2: Check if any synonym (min 4 chars) is contained in the input
    # This handles cases like "ARGOR-HERAEUS S.A. Switzerland"
    # Require minimum length to avoid false positives from short matches
    for canonical, variants in PRODUCER_SYNONYM_MAP.items():
        for variant in variants:
            if len(variant) >= 4:  # Only match meaningful substrings
                # Check if variant is a substring of normalized input
                if variant in normalized:
                    return canonical

    # Strategy 3: Check if canonical name appears in input
    for canonical in PRODUCER_SYNONYM_MAP.keys():
        canon_normalized = canonicalize_producer_key(canonical)
        if len(canon_normalized) >= 4 and canon_normalized in normalized:
            return canonical

    # Strategy 4: Fuzzy match for common OCR typos (Levenshtein distance 1)
    # e.g., "unicore" → "umicore", "Hereus" → "heraeus"
    for canonical, variants in PRODUCER_SYNONYM_MAP.items():
        for variant in variants:
            if len(variant) >= 5 and _is_close_match(normalized, variant):
                return canonical

    return normalized


def _is_close_match(s1: str, s2: str, max_distance: int = 1) -> bool:
    """Check if two strings are within edit distance (Levenshtein).

    Simple implementation for short strings typical of producer names.
    """
    if abs(len(s1) - len(s2)) > max_distance:
        return False
    if s1 == s2:
        return True

    # Simple single-character difference check
    if len(s1) == len(s2):
        diffs = sum(c1 != c2 for c1, c2 in zip(s1, s2, strict=False))
        return diffs <= max_distance

    # One character insertion/deletion
    longer, shorter = (s1, s2) if len(s1) > len(s2) else (s2, s1)
    for i in range(len(longer)):
        if longer[:i] + longer[i + 1 :] == shorter:
            return True

    return False


def get_producer_candidates(value: str | None) -> set[str]:
    """Extract all possible producer name variants from text.

    Args:
        value: Text potentially containing producer names

    Returns:
        Set of normalized producer name candidates
    """
    candidates: set[str] = set()
    if value is None:
        return candidates
    text = str(value)
    segments = [text]
    match = re.search(r"\(Paddle:\s*([^)]+)\)", text)
    if match:
        segments.append(match.group(1))
    for segment in segments:
        normalized = normalize_producer(segment)
        if normalized:
            candidates.add(normalized)
    return candidates


def normalize_unit(value: str | None) -> str | None:
    """Normalize weight unit to standard abbreviation.

    Args:
        value: Unit string (e.g., 'grams', 'kg', 'ounce')

    Returns:
        Normalized unit ('g', 'kg', 'oz') or None
    """
    if value is None:
        return None
    unit = str(value).strip().lower()
    mapping = {
        "gram": "g",
        "grams": "g",
        "g": "g",
        "kg": "kg",
        "kilo": "kg",
        "kilogram": "kg",
        "kilograms": "kg",
        "oz": "oz",
        "ounce": "oz",
        "ozt": "oz",
    }
    return mapping.get(unit, unit)


def weight_to_grams(weight_value: str | float | None, unit_value: str | None) -> float | None:
    """Convert weight to grams regardless of original unit.

    Args:
        weight_value: Numeric weight value or string with value and unit
        unit_value: Optional unit string (used if not in weight_value)

    Returns:
        Weight in grams or None if conversion fails
    """
    if weight_value is None:
        return None
    unit = unit_value
    if isinstance(weight_value, str):
        match = re.match(
            r"(?P<value>-?\d+(?:[.,]\d+)?)(?:\s*(?P<unit>[a-zA-Z]+))?", weight_value.strip()
        )
        if not match:
            return None
        value = float(match.group("value").replace(",", "."))
        unit = unit or match.group("unit")
    else:
        try:
            value = float(weight_value)
        except (TypeError, ValueError):
            return None
    unit_norm = (unit or "g").lower()
    if unit_norm in {"g", "gram", "grams"}:
        return value
    if unit_norm in {"kg", "kilo", "kilogram", "kilograms"}:
        return value * 1000
    if unit_norm in {"oz", "ounce", "ozt"}:
        return value * 31.1034768
    return value


def normalize_fineness_value(value: str | float | None) -> float | None:
    """Normalize fineness value to decimal (0.xxx format).

    Args:
        value: Fineness as string or number (e.g., '999', '0.999', 999)

    Returns:
        Normalized fineness as decimal (e.g., 0.999) or None
    """
    if value is None:
        return None
    try:
        if isinstance(value, str):
            cleaned = re.sub(r"[^0-9.,]", "", value).replace(",", ".").strip()
            if not cleaned:
                return None
            fineness = float(cleaned)
        else:
            fineness = float(value)
    except (TypeError, ValueError):
        return None
    while fineness > 2:
        fineness /= 10
    return fineness if fineness > 0 else None
