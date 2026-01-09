"""Producer synonym mappings and normalization utilities for strategy comparison."""

import re


def canonicalize_producer_key(value: str) -> str:
    """Normalize producer strings for fuzzy comparisons."""
    cleaned = re.sub(r"[^a-z0-9]", " ", value.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


RAW_PRODUCER_SYNONYMS = {
    "argor heraeus": {"argor heraeus", "argor-heraeus", "argor", "argor sa", "argor group"},
    "heraeus": {"heraeus", "heraeus sa", "heraeus gmbh"},
    "valcambi": {"valcambi", "valcambi sa", "valcambi suisse"},
    "umicore": {"umicore", "umicore sa"},
    "mks pamp": {"mks pamp", "pamp", "mks", "pamp suisse"},
    "metalor": {"metalor", "metalor technologies"},
    "credit suisse": {"credit suisse", "cs", "credit-suisse"},
    "ubs": {"ubs", "ubs ag"},
    "clariden leu": {"clariden leu", "clariden"},
    "raiffeisen": {"raiffeisen", "raiffeisenbank"},
    "commerzbank": {"commerzbank"},
    "degussa": {"degussa", "degussas"},
    "kantonalbank": {"kantonalbank", "kantonal bank"},
    "metaux precieux s a": {"metaux precieux", "metaux precieux s.a.", "metaux precieux sa"},
    "perth mint": {"perth mint", "the perth mint"},
    "rcm": {"rcm", "royal canadian mint"},
    "asahi": {"asahi", "asahi refining"},
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
    for canonical, variants in PRODUCER_SYNONYM_MAP.items():
        if normalized in variants:
            return canonical
    return normalized


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
    if unit_norm in {"kg", "kilogram", "kilograms"}:
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
