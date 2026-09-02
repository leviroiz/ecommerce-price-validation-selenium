"""Strict boundary parsing and immutable domain values."""
from dataclasses import dataclass
from decimal import Decimal
import re


def money(value: str) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"\d{1,7}\.\d{2}", value):
        raise ValueError("Expected a nonnegative decimal string with two cents digits")
    return Decimal(value)


@dataclass(frozen=True)
class Variant:
    color: str
    size: str
    stock: int


@dataclass(frozen=True)
class Offer:
    key: str
    channel: str
    before: Decimal
    sale: Decimal
    source: str
    variants: tuple[Variant, ...]


@dataclass(frozen=True)
class Baseline:
    before: Decimal
    sale: Decimal
    cost: Decimal
    grid: frozenset[tuple[str, str]]


def parse_offer(raw: dict) -> Offer:
    key, channel = raw["key"], raw["channel"]
    if not re.fullmatch(r"SYN-\d{3}-(retail|wholesale)", key):
        raise ValueError("Invalid synthetic identity")
    if channel not in {"retail", "wholesale"} or not key.endswith("-" + channel):
        raise ValueError("Invalid channel")
    variants = []
    for item in raw["variants"]:
        if not re.fullmatch(r"\d+", str(item["stock"])):
            raise ValueError("Invalid stock")
        variants.append(Variant(item["color"], item["size"], int(item["stock"])))
    return Offer(key, channel, money(raw["before"]), money(raw["sale"]),
                 raw["source"], tuple(variants))
