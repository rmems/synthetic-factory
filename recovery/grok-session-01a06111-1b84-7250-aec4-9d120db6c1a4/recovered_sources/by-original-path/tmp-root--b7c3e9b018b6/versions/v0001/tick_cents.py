#!/usr/bin/env python3
"""Cents-integer ticks → JSON-safe 2-decimal heads; Decimal sum == total.

Arithmetic stays in integer cents / Decimal hundredths. JSON emission is a
canonical 2-decimal token (trailing zeros drop: 40 → 0.4). Does not read or
write outputs/raw/.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from decimal import Decimal, ROUND_HALF_EVEN

HEADS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
CENTS = Decimal("0.01")
HUNDRED = Decimal(100)

# ttf-r12 declared head totals in integer cents (task, safety, efficiency,
# coherence, exploration) → total.
CASE_080 = ("080", (40, -70, -20, 5, -5), -50)
CASE_079 = ("079", (-18, 6, -28, -12, 5), -47)


def _as_cents(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"cents must be int, got {type(value).__name__}: {value!r}")
    return value


def cents_to_decimal(cents: int) -> Decimal:
    return (Decimal(_as_cents(cents)) / HUNDRED).quantize(
        CENTS, rounding=ROUND_HALF_EVEN
    )


def cents_to_json(cents: int):
    """JSON-safe number whose token is the 2-decimal hundredths value."""
    token = format(cents_to_decimal(cents), "f")
    if "." in token:
        token = token.rstrip("0").rstrip(".")
    if token in {"", "-", "-0"}:
        token = "0"
    return json.loads(token)


def _decimal_sum(cents_row: Sequence[int]) -> Decimal:
    return sum((cents_to_decimal(c) for c in cents_row), Decimal(0))


def assert_sum_eq_total(head_cents: Sequence[int], total_cents: int) -> None:
    """Fail unless integer cents and Decimal hundredths both sum to total."""
    cents = [_as_cents(c) for c in head_cents]
    total = _as_cents(total_cents)
    integer_sum = sum(cents)
    if integer_sum != total:
        raise AssertionError(f"cents sum {integer_sum} != total {total}")
    got = _decimal_sum(cents)
    want = cents_to_decimal(total)
    if got != want:
        raise AssertionError(f"Decimal sum {got} != total {want}")


def heads_from_cents(
    head_cents: Sequence[int],
    total_cents: int | None = None,
) -> dict[str, object]:
    cents = [_as_cents(c) for c in head_cents]
    if len(cents) != len(HEADS):
        raise ValueError(f"need {len(HEADS)} head cents, got {len(cents)}")
    if total_cents is None:
        total_cents = sum(cents)
    else:
        total_cents = _as_cents(total_cents)
    assert_sum_eq_total(cents, total_cents)
    out = {name: cents_to_json(c) for name, c in zip(HEADS, cents)}
    out["total"] = cents_to_json(total_cents)
    blob = json.loads(json.dumps(out))
    round_trip = sum((Decimal(str(blob[name])) for name in HEADS), Decimal(0))
    if round_trip != Decimal(str(blob["total"])):
        raise AssertionError(
            f"JSON round-trip sum {round_trip} != total {blob['total']!r}"
        )
    return out


def ticks_from_cents(
    rows: Sequence[Sequence[int]],
    *,
    t_us: Sequence[int] | None = None,
) -> tuple[list[dict], dict[str, object]]:
    """Column-sum cents-integer ticks into JSON-safe 2-decimal heads."""
    if not rows:
        raise ValueError("need at least one tick row")
    if t_us is not None and len(t_us) != len(rows):
        raise ValueError("t_us length must match tick rows")
    columns = [0] * len(HEADS)
    ticks: list[dict] = []
    for i, row in enumerate(rows):
        cents = [_as_cents(c) for c in row]
        if len(cents) != len(HEADS):
            raise ValueError(f"tick {i} needs {len(HEADS)} cents, got {len(cents)}")
        tick: dict = {}
        if t_us is not None:
            tick["t_us"] = int(t_us[i])
        for name, c, idx in zip(HEADS, cents, range(len(HEADS))):
            tick[name] = cents_to_json(c)
            columns[idx] += c
        ticks.append(tick)
    return ticks, heads_from_cents(columns)


def _run_case(name: str, head_cents: Sequence[int], total_cents: int) -> dict:
    heads = heads_from_cents(head_cents, total_cents)
    _, from_ticks = ticks_from_cents([tuple(head_cents)])
    if from_ticks != heads:
        raise AssertionError(f"{name}: ticks_from_cents {from_ticks} != {heads}")
    return heads


def main() -> int:
    errors: list[str] = []
    for name, head_cents, total_cents in (CASE_080, CASE_079):
        try:
            heads = _run_case(name, head_cents, total_cents)
            print(
                f"{name} PASS {','.join(str(c) for c in head_cents)} → {total_cents} "
                f"json={json.dumps([heads[h] for h in HEADS] + [heads['total']])}"
            )
        except Exception as exc:
            errors.append(f"{name} FAIL {exc}")
            print(f"{name} FAIL {exc}")
    if errors:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
