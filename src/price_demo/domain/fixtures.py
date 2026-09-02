"""Deterministic invented catalog; no production data or imported HTML."""
import csv
import json
from copy import deepcopy
from pathlib import Path
from .prices import CELLS, FIELDS, SIDES, UnsafeState, reference, regular

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "fixtures"


def expected_catalog():
    result = {}
    with (FIXTURES / "expected.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["reference", *FIELDS]:
            raise UnsafeState("Invalid expected fixture headers")
        for row in reader:
            ref = reference(row.pop("reference"))
            if ref in result:
                raise UnsafeState("Duplicate expected reference")
            regular(row)
            result[ref] = {
                "reference": ref, "name": "Objeto ficticio " + ref,
                "regular": row,
                "xg": {side: {cell: row[field] for cell in CELLS}
                       for side, field in zip(SIDES, ("wholesale_sale", "retail_sale"))},
                "stock": {cell: 3 for cell in CELLS},
            }
    return result


def initial_catalog():
    result = deepcopy(expected_catalog())
    changes = json.loads((FIXTURES / "scenarios.json").read_text(encoding="utf-8"))
    for ref, change in changes.items():
        product = result[ref]
        for section, values in change.items():
            if section == "xg":
                for side, cells in values.items():
                    product["xg"][side].update(cells)
            else:
                product[section].update(values)
    return result


def approvals():
    result = json.loads((FIXTURES / "approved.json").read_text(encoding="utf-8"))
    if not isinstance(result, list) or len(set(result)) != len(result):
        raise UnsafeState("Invalid approval list")
    return {reference(item) for item in result}
