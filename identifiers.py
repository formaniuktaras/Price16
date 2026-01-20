import hashlib
import re
from typing import Set

_TRANSLIT_TABLE = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "є": "ie",
    "ж": "zh",
    "з": "z",
    "и": "y",
    "і": "i",
    "ї": "yi",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ь": "",
    "ю": "yu",
    "я": "ya",
    "ъ": "",
    "ы": "y",
    "э": "e",
    "ё": "yo",
}

_ALLOWED_RE = re.compile(r"[^0-9A-Za-z]+")


def _transliterate_ascii(value: str) -> str:
    result = []
    for ch in value:
        lower = ch.lower()
        if "a" <= lower <= "z" or lower.isdigit():
            result.append(lower)
            continue
        if lower in _TRANSLIT_TABLE:
            result.append(_TRANSLIT_TABLE[lower])
            continue
        result.append("")
    return "".join(result)


def clean_id(raw: str, max_len: int = 32) -> str:
    if raw is None:
        raw_value = ""
    else:
        raw_value = str(raw)
    trimmed = raw_value.strip()
    transliterated = _transliterate_ascii(trimmed) if trimmed else ""
    cleaned = _ALLOWED_RE.sub("", transliterated).upper()
    if not cleaned:
        cleaned = "ID"

    try:
        max_len = int(max_len)
    except (TypeError, ValueError):
        max_len = 32

    if max_len <= 0:
        return ""

    if len(cleaned) > max_len:
        suffix = hashlib.sha1(raw_value.encode("utf-8")).hexdigest()[:6].upper()
        if max_len <= len(suffix):
            return suffix[:max_len]
        prefix = cleaned[: max_len - len(suffix)]
        cleaned = f"{prefix}{suffix}"
    return cleaned


def make_unique_id(candidate: str, existing: Set[str]) -> str:
    base = str(candidate)
    if base not in existing:
        return base
    counter = 2
    while True:
        proposed = f"{base}{counter}"
        if proposed not in existing:
            return proposed
        counter += 1
