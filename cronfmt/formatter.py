"""Normalize messy cron expressions into a canonical, comparable form."""

from dataclasses import dataclass, field as dc_field
from typing import Callable, Dict, Optional, Tuple


class CronFormatError(ValueError):
    """Raised when an expression can't be parsed as a cron schedule."""


@dataclass
class Field:
    name: str
    bounds: Tuple[int, int]
    names: Dict[str, str] = dc_field(default_factory=dict)
    canonicalize: Optional[Callable[[int], int]] = None


MONTH_NAMES = {
    name: name
    for name in ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
}

DOW_NAMES = {name: name for name in ("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT")}


def _fold_sunday(value: int) -> int:
    # both 0 and 7 mean Sunday; 7 is the common "messy" spelling
    return 0 if value == 7 else value


FIELDS = (
    Field("minute", (0, 59)),
    Field("hour", (0, 23)),
    Field("day of month", (1, 31)),
    Field("month", (1, 12), names=MONTH_NAMES),
    Field("day of week", (0, 7), names=DOW_NAMES, canonicalize=_fold_sunday),
)

# some schedulers (Quartz, several cron forks) prepend a seconds column
# ahead of minute; accept it as an optional 6th leading field
FIELDS_WITH_SECONDS = (Field("second", (0, 59)),) + FIELDS

MACROS = {
    "@yearly",
    "@annually",
    "@monthly",
    "@weekly",
    "@daily",
    "@midnight",
    "@hourly",
    "@reboot",
}


def format_cron(expression: str) -> str:
    """Return a canonical rendering of a cron expression.

    Accepts the standard 5-field form (minute hour day-of-month month
    day-of-week) or a 6-field form with a leading seconds column.
    Collapses stray whitespace, strips leading zeros, dedupes and sorts
    comma lists, folds day/month name casing, and folds day-of-week 7
    down to 0. Raises CronFormatError on anything it can't make sense of.
    """
    if not isinstance(expression, str):
        raise CronFormatError(f"expected a string, got {type(expression).__name__}")

    stripped = expression.strip()
    if not stripped:
        raise CronFormatError("empty cron expression")

    if stripped.startswith("@"):
        macro = stripped.lower()
        if macro not in MACROS:
            raise CronFormatError(f"unrecognized macro '{stripped}'")
        return macro

    tokens = stripped.split()
    if len(tokens) == len(FIELDS_WITH_SECONDS):
        fields = FIELDS_WITH_SECONDS
    elif len(tokens) == len(FIELDS):
        fields = FIELDS
    else:
        raise CronFormatError(
            f"expected {len(FIELDS)} fields (minute hour day-of-month month day-of-week) "
            f"or {len(FIELDS_WITH_SECONDS)} with a leading seconds field, "
            f"got {len(tokens)}: '{expression}'"
        )

    normalized = [_normalize_field(token, field) for token, field in zip(tokens, fields)]
    return " ".join(normalized)


def _normalize_field(token: str, field: Field) -> str:
    parts = [p for p in token.split(",") if p != ""]
    if not parts:
        raise CronFormatError(f"empty value in {field.name} field")

    seen = set()
    pieces = []
    for part in parts:
        piece = _normalize_piece(part, field)
        if piece not in seen:
            seen.add(piece)
            pieces.append(piece)

    pieces.sort(key=_sort_key)
    return ",".join(pieces)


def _sort_key(piece: str):
    if piece.isdigit():
        return (0, int(piece), piece)
    return (1, 0, piece)


def _normalize_piece(raw: str, field: Field) -> str:
    raw = raw.strip()
    if not raw:
        raise CronFormatError(f"empty value in {field.name} field")

    step = None
    if "/" in raw:
        base, step_str = raw.split("/", 1)
        step_str = step_str.strip()
        if not step_str.isdigit() or int(step_str) == 0:
            raise CronFormatError(f"invalid step '{step_str}' in {field.name} field")
        step = str(int(step_str))
        raw = base.strip()

    if raw == "*":
        base_out = "*"
    elif "-" in raw:
        lo, hi = raw.split("-", 1)
        base_out = f"{_normalize_value(lo, field)}-{_normalize_value(hi, field)}"
    else:
        base_out = _normalize_value(raw, field)

    return f"{base_out}/{step}" if step is not None else base_out


def _normalize_value(token: str, field: Field) -> str:
    token = token.strip()
    if not token:
        raise CronFormatError(f"empty value in {field.name} field")

    upper = token.upper()
    if upper in field.names:
        return upper

    if not token.isdigit():
        raise CronFormatError(f"invalid value '{token}' in {field.name} field")

    value = int(token)
    if field.canonicalize is not None:
        value = field.canonicalize(value)

    low, high = field.bounds
    if not (low <= value <= high):
        raise CronFormatError(
            f"value {token} out of range for {field.name} field (expected {low}-{high})"
        )

    return str(value)
