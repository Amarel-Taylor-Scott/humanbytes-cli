#!/usr/bin/env python3
"""humanbytes: parse and format human-readable byte sizes.

Supports both IEC units (KiB, MiB, GiB, ...) based on 1024-byte prefixes and
SI units (kB, MB, GB, ...) based on 1000-byte prefixes.
"""

from __future__ import annotations

import argparse
import decimal
import re
import sys
from typing import Iterable

__all__ = ["format_bytes", "parse_bytes", "main"]

# IEC binary prefixes (base 1024)
IEC_UNITS: tuple[str, ...] = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
# SI decimal prefixes (base 1000)
SI_UNITS: tuple[str, ...] = ("B", "kB", "MB", "GB", "TB", "PB", "EB")

# Pre-compile a case-insensitive regex for parsing.
# Examples that match: "1.5 GiB", "1.5GiB", "1.5 GB", "-42 kiB", "0 B"
_PARSE_RE = re.compile(
    r"^\s*([+-]?\d+(?:\.\d+)?)\s*([KMGTPE]?i?[bB])\s*$",
    re.IGNORECASE,
)


def _get_units(unit_system: str) -> tuple[str, ...]:
    system = unit_system.upper()
    if system == "IEC":
        return IEC_UNITS
    if system == "SI":
        return SI_UNITS
    raise ValueError(f"unit_system must be 'IEC' or 'SI', got {unit_system!r}")


def _base(unit_system: str) -> int:
    return 1024 if unit_system.upper() == "IEC" else 1000


def _find_unit_index(units: Iterable[str], unit: str) -> int:
    """Return the index of *unit* in *units* (case-insensitive)."""
    unit_lower = unit.lower()
    for idx, candidate in enumerate(units):
        if candidate.lower() == unit_lower:
            return idx
    raise ValueError(f"unrecognized unit {unit!r}")


def parse_bytes(value: str | int) -> int:
    """Parse a human-readable byte size into an integer number of bytes.

    Both IEC (KiB, MiB, GiB, ...) and SI (kB, MB, GB, ...) units are accepted.
    The unit letter is case-insensitive and whitespace around the number is
    allowed.  Returns a (possibly negative) ``int``.

    Raises TypeError when passed a non-string, non-int (e.g. float), to guard
    against silent truncation of fractional byte counts.

    Examples:
        >>> parse_bytes("1.5 GiB")
        1610612736
        >>> parse_bytes("500 MB")
        500000000
        >>> parse_bytes("-1 kiB")
        -1024
    """
    # Reject floats and bools before they can be string-coerced into a form
    # that would raise ValueError.  isinstance(bool, int) is True, so bools
    # must be excluded explicitly.
    if not isinstance(value, str) and not (isinstance(value, int) and not isinstance(value, bool)):
        raise TypeError(f"expected str or int, got {type(value).__name__!r}")

    if isinstance(value, int):
        return value

    text = str(value).strip()
    if not text:
        raise ValueError("empty byte size")

    # Plain integer string (no unit) -> bytes.
    if re.fullmatch(r"[+-]?\d+", text):
        return int(text)

    match = _PARSE_RE.match(text)
    if not match:
        raise ValueError(f"cannot parse byte size {value!r}")

    number_str, unit = match.groups()
    number = decimal.Decimal(number_str)

    unit_lower = unit.lower()
    if "i" in unit_lower:
        system = "IEC"
    else:
        system = "SI"

    units = _get_units(system)
    idx = _find_unit_index(units, unit)
    multiplier = decimal.Decimal(_base(system)) ** idx
    result = number * multiplier

    # Round to the nearest integer to tolerate floating-point-like Decimal
    # remainders (e.g. 1.1 GiB -> 1181116006.4).
    return int(result.to_integral_value(rounding=decimal.ROUND_HALF_EVEN))


def format_bytes(
    n: int,
    *,
    unit_system: str = "IEC",
    precision: int = 2,
    min_unit_index: int = 0,
) -> str:
    """Format an integer byte count as a human-readable string.

    Args:
        n: Number of bytes (may be negative).
        unit_system: ``"IEC"`` (default, base-1024) or ``"SI"`` (base-1000).
        precision: Number of fractional digits to show when a scaled unit is
            used.  ``0`` means no fractional part.
        min_unit_index: Lowest unit index to consider (0 = bytes).  Useful when
            you always want at least KiB, for example.

    Examples:
        >>> format_bytes(1610612736)
        '1.50 GiB'
        >>> format_bytes(500000000, unit_system="SI")
        '500.00 MB'
        >>> format_bytes(0)
        '0 B'
    """
    if not isinstance(n, int):
        raise TypeError("n must be an integer number of bytes")
    if precision < 0:
        raise ValueError("precision must be non-negative")

    system = unit_system.upper()
    units = _get_units(system)
    base = _base(system)

    negative = n < 0
    magnitude = abs(n)

    # Choose the largest unit that keeps the scaled value >= 1, respecting the
    # minimum unit index.  Note: zero deliberately falls through to unit index
    # 0 (bytes) so that format_bytes(0, min_unit_index=N) correctly returns
    # "0 B" — asking for at least KiB makes no sense for zero bytes.
    idx = min_unit_index
    max_idx = len(units) - 1
    if magnitude == 0:
        idx = 0
    else:
        while idx < max_idx and magnitude >= base ** (idx + 1):
            idx += 1

    scaled = magnitude / (base ** idx)

    # Format with the requested precision.  When the scaled value is an
    # integer and we are at the byte unit, drop the fractional part for a
    # cleaner display.  Otherwise keep precision so round-trips stay exact.
    if idx == 0 and scaled == int(scaled):
        formatted = f"{int(scaled)} {units[idx]}"
    else:
        formatted = f"{scaled:.{precision}f} {units[idx]}"

    return f"-{formatted}" if negative else formatted


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="humanbytes",
        description="Parse and format human-readable byte sizes.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    parse_cmd = sub.add_parser("parse", help="parse a human-readable size")
    parse_cmd.add_argument("value", help="e.g. '1.5 GiB' or '500 MB'")

    format_cmd = sub.add_parser("format", help="format a byte count")
    format_cmd.add_argument("value", type=int, help="integer number of bytes")
    format_cmd.add_argument(
        "--si",
        action="store_true",
        help="use SI (base-1000) units instead of IEC (base-1024)",
    )
    format_cmd.add_argument(
        "--precision",
        type=int,
        default=2,
        help="number of fractional digits (default: 2)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "parse":
        try:
            print(parse_bytes(args.value))
        except ValueError as exc:
            parser.error(str(exc))
    elif args.command == "format":
        system = "SI" if args.si else "IEC"
        print(format_bytes(args.value, unit_system=system, precision=args.precision))
    else:  # pragma: no cover
        parser.error(f"unknown command {args.command!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
