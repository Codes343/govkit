"""Cleaning helpers.

Customers can hit these APIs for free. What they are actually paying for is not
having to discover, one field at a time, that ``awardCeiling`` is sometimes the
*string* ``"none"``, that dates arrive as ``"Sep 19, 2019 12:00:00 AM EDT"``,
and that descriptions are HTML fragments with ``&mdash;`` in them.
"""

from __future__ import annotations

import html
import re
from datetime import date, datetime

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_RE = re.compile(r"\n{3,}")

# Values various federal APIs use to mean "no value", as strings.
_NULLISH = frozenset({"", "none", "null", "n/a", "na", "not applicable", "-"})

_DATE_FORMATS = (
    "%Y-%m-%d-%H-%M-%S",  # grants.gov *Str fields
    "%Y-%m-%d",
    "%m/%d/%Y",  # grants.gov search2 openDate/closeDate
    "%Y%m%d",  # openFDA
    "%b %d, %Y %I:%M:%S %p",  # grants.gov verbose form, tz already stripped
)

# strptime's %Z only understands UTC/GMT and the local zone, so "EDT"/"PST"
# would fail to parse. Strip a trailing alphabetic zone abbreviation first.
_TZ_SUFFIX_RE = re.compile(r"\s+[A-Z]{2,5}$")


def clean_str(value: object) -> str | None:
    """Trim a string and collapse the many spellings of 'empty' to None."""
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in _NULLISH else text


def clean_text(value: object) -> str | None:
    """Turn an HTML fragment into readable plain text."""
    if value is None:
        return None
    text = str(value)
    # <br> and </p> carry the only line structure these fields have; keep it.
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    # Replace with a space, not "": "a<span>b" must not become "ab". The
    # whitespace collapse below removes the spaces this introduces elsewhere.
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text)
    text = _BLANK_RE.sub("\n\n", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return clean_str(text)


def clean_date(value: object) -> str | None:
    """Parse any of the federal date spellings into a plain ISO date."""
    text = clean_str(value)
    if text is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    candidate = _TZ_SUFFIX_RE.sub("", text)
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(candidate, fmt).date().isoformat()
        except ValueError:
            continue
    # ISO-ish with a time component or timezone suffix.
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return text  # preserve the raw value rather than silently dropping data


def clean_money(value: object) -> float | None:
    """Coerce a currency-ish field to a float, tolerating '$1,000' and 'none'."""
    text = clean_str(value)
    if text is None:
        return None
    text = text.replace("$", "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def clean_int(value: object) -> int | None:
    text = clean_str(value)
    if text is None:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def clean_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    text = clean_str(value)
    if text is None:
        return None
    lowered = text.lower()
    if lowered in {"true", "yes", "y", "1"}:
        return True
    if lowered in {"false", "no", "n", "0"}:
        return False
    return None


def describe_all(items: object, key: str = "description") -> list[str]:
    """Flatten the ``[{'id': .., 'description': ..}]`` shape .gov APIs love."""
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for item in items:
        text = clean_str(item.get(key)) if isinstance(item, dict) else clean_str(item)
        if text:
            out.append(text)
    return out


def compact(record: dict[str, object]) -> dict[str, object]:
    """Drop keys whose value is None, keeping empty lists (they mean 'checked')."""
    return {k: v for k, v in record.items() if v is not None}
