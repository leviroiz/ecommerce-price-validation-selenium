"""Pure, conservative demonstration policy; no browser dependencies."""
from dataclasses import dataclass
from decimal import Decimal
from .models import Baseline, Offer

CENT = Decimal("0.01")


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    unit_delta: Decimal = Decimal("0.00")
    stock_exposure: Decimal = Decimal("0.00")


def decide(offer: Offer, baseline: Baseline | None) -> Decision:
    def blocked(reason):
        return Decision("blocked", reason)

    if baseline is None:
        return blocked("missing_baseline")
    amounts = (offer.before, offer.sale, baseline.before, baseline.sale, baseline.cost)
    if any(not n.is_finite() or n <= 0 for n in amounts):
        return blocked("invalid_amount")
    if offer.sale > offer.before or baseline.sale > baseline.before:
        return blocked("inverted_de_por")
    if abs(offer.before - baseline.before) > CENT:
        return blocked("de_changed")
    pairs = [(v.color, v.size) for v in offer.variants]
    if (len(set(pairs)) != len(pairs) or set(pairs) != baseline.grid
            or not any(size == "XG" for _, size in pairs)):
        return blocked("uncertain_grid")
    if any(type(v.stock) is not int or v.stock < 0 for v in offer.variants):
        return blocked("invalid_stock")
    delta = baseline.sale - offer.sale
    if abs(delta) <= CENT:
        return Decision("unchanged", "within_cent_tolerance")
    if offer.source != "synthetic_api_drift":
        return blocked("unconfirmed_cause")
    stock = sum(v.stock for v in offer.variants)
    if stock == 0 or not any(v.size == "XG" and v.stock > 0 for v in offer.variants):
        return blocked("no_sellable_xg_stock")
    # Explicit demo-only thresholds: 25% change and at least 10% gross margin.
    if abs(delta) / baseline.sale > Decimal("0.25"):
        return blocked("change_exceeds_demo_limit")
    if (baseline.sale - baseline.cost) / baseline.sale < Decimal("0.10"):
        return blocked("margin_below_demo_limit")
    return Decision("correct", "confirmed_por_drift", delta, delta * stock)
