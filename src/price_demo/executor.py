"""Reconcile current state on every run; never trust an old success marker."""
from dataclasses import asdict, replace
from .rules import decide


def run(catalog, baselines, audit, *, apply=False):
    results = []
    for key in catalog.keys():
        try:
            current = catalog.read(key)
            baseline = baselines.get(key)
            decision = decide(current, baseline)
            event = {"key": key, "mode": "apply" if apply else "dry_run",
                     "before": asdict(current), "decision": asdict(decision),
                     "target": str(baseline.sale) if baseline else None}
            audit.record(status="evaluated", **event)
            if decision.action == "correct" and apply:
                # Includes stock, grid, source and both prices in optimistic comparison.
                if catalog.read(key) != current:
                    raise RuntimeError("State changed before write")
                audit.record(status="intent", **event)
                catalog.write(key, baseline.sale)
                catalog.refresh()
                observed = catalog.read(key)
                if observed != replace(current, sale=baseline.sale):
                    raise RuntimeError("Post-write verification failed")
                audit.record(status="verified", after=asdict(observed), **event)
            results.append(decision.action)
        except Exception as error:
            # No blind retry/rollback: the saved state may have changed.
            audit.record(status="failed", key=key, error_type=type(error).__name__)
            raise
    return results
