"""Helpers for reading Actor input.

Apify input arrives as whatever the caller sent. The Console UI sends the types
declared in input_schema.json, but API and MCP callers routinely send a
comma-separated string where an array is expected, omit optional fields, or send
an empty string for "no value". Every actor needs the same coercions, so they
live here rather than being re-typed in each entrypoint.
"""

from __future__ import annotations

from typing import Any


def as_list(value: object) -> list[str] | None:
    """Coerce an array-ish input to a list of non-empty strings, or None.

    Accepts a real list, or a comma-separated string (what most API callers
    send). Returns None rather than [] so callers can treat "not supplied" and
    "supplied but empty" identically.
    """
    if value is None:
        return None
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        parts = [str(p).strip() for p in value]
    else:
        return None
    parts = [p for p in parts if p]
    return parts or None


def as_text(value: object) -> str | None:
    """Trim a free-text input; blank becomes None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def as_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
    """Clamp a numeric input into range, falling back to default if unusable.

    Never raises: a malformed maxItems should not fail a paid run, and silently
    clamping is friendlier than erroring on a value the user can't see.
    """
    if value is None or value == "":
        return default
    try:
        parsed = int(float(value))  # tolerates "500" and 500.0 alike
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))


def invalid_choices(values: list[str] | None, allowed: tuple[str, ...]) -> list[str]:
    """Return any values outside `allowed`, for a clear up-front error."""
    if not values:
        return []
    return [v for v in values if v not in allowed]


def as_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get(raw: dict[str, Any], key: str, default: object = None) -> Any:
    """Read a key from input that may itself be None."""
    return (raw or {}).get(key, default)
