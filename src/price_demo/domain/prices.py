"""Exact decimal comparisons; never infer a pricing policy."""
from decimal import Decimal, InvalidOperation
import re

FIELDS = ("wholesale_list", "wholesale_sale", "retail_list", "retail_sale")
SIDES = ("atacado", "varejo")
CELLS = ("Ciano|T1", "Ciano|T2", "Ambar|T1", "Ambar|T2")


class UnsafeState(ValueError):
    """Missing, ambiguous or changed state: stop before writing."""


def reference(value):
    if not isinstance(value, str) or not re.fullmatch(r"DEMO-[0-9]{3}", value):
        raise UnsafeState("Invalid synthetic reference")
    return value


def money(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+[.,][0-9]{2}", value):
        raise UnsafeState("Unreadable price")
    try:
        result = Decimal(value.replace(",", "."))
    except InvalidOperation as exc:
        raise UnsafeState("Unreadable price") from exc
    if not result.is_finite() or result <= 0:
        raise UnsafeState("Price must be positive")
    return result


def regular(values):
    if set(values) != set(FIELDS):
        raise UnsafeState("Expected exactly four price fields")
    return {key: money(values[key]) for key in FIELDS}


def grid(values):
    if not isinstance(values, dict) or not values:
        raise UnsafeState("Missing grid structure")
    return {key: money(value) for key, value in values.items()}


def compare_regular(actual, expected):
    return "OK" if regular(actual) == regular(expected) else "DIVERGENTE"


def compare_grid(actual, expected):
    found, target = grid(actual), grid(expected)
    if found.keys() != target.keys():
        raise UnsafeState("Grid topology differs")
    if all(value is None for value in found.values()):
        return "SEM_VALORES", ()
    differences = tuple(key for key in target if found[key] != target[key])
    return ("DIVERGENTE" if differences else "OK"), differences


def same_prices(left, right):
    return (regular(left["regular"]) == regular(right["regular"])
            and all(grid(left["xg"][side]) == grid(right["xg"][side]) for side in SIDES))
