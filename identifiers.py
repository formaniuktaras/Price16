import hashlib
import re
from dataclasses import dataclass
from typing import Set

_DISALLOWED_KEY_RE = re.compile(r"[^A-Z0-9_]+")


@dataclass(frozen=True)
class FieldItem:
    key: str
    label: str
    enabled: bool



def sanitize_key(raw: str) -> str:
    if raw is None:
        raw_value = ""
    else:
        raw_value = str(raw)
    trimmed = raw_value.strip()
    cleaned = _ALLOWED_RE.sub("", trimmed).upper()
    return cleaned or "ID"


def clean_id(raw: str, max_len: int = 32) -> str:
    if raw is None:
        raw_value = ""
    else:
        raw_value = str(raw)
    cleaned = _DISALLOWED_KEY_RE.sub("", raw_value.strip().upper())
    return cleaned or "ID"


def clean_id(raw: str, max_len: int = 32) -> str:
    cleaned = sanitize_key(raw)
    try:
        max_len = int(max_len)
    except (TypeError, ValueError):
        max_len = 32

    if max_len <= 0:
        return ""

    if len(cleaned) > max_len:
        suffix = hashlib.sha1(str(raw).encode("utf-8")).hexdigest()[:6].upper()
        if max_len <= len(suffix):
            return suffix[:max_len]
        prefix = cleaned[: max_len - len(suffix)]
        cleaned = f"{prefix}{suffix}"
    return cleaned


def ensure_unique_key(key: str, existing: Set[str]) -> str:
    base = str(key)
    if base not in existing:
        return base
    counter = 2
    while True:
        proposed = f"{base}{counter}"
        if proposed not in existing:
            return proposed
        counter += 1


def ensure_unique_key(key: str, existing: Set[str]) -> str:
    return make_unique_id(key, existing)
