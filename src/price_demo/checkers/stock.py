"""Robot C: intersect only divergent cells, not total product stock."""
from ..domain.prices import UnsafeState


def cross_stock(xg_rows, stock):
    grouped = {}
    unreadable = {row["reference"] for row in xg_rows if row["status"] == "ERRO_LEITURA"}
    for row in xg_rows:
        if row["status"] == "DIVERGENTE":
            grouped.setdefault(row["reference"], set()).update(row["divergent_cells"].split(";"))
    rows = []
    for ref, cells in sorted(grouped.items()):
        active, empty, unknown = 0, 0, 0
        for cell in cells:
            quantity = stock.get(ref, {}).get(cell)
            if type(quantity) is not int or quantity < 0:
                unknown += 1
            elif quantity > 0:
                active += 1
            else:
                empty += 1
        status = ("ERRO_LEITURA" if unknown or ref in unreadable else
                  "DIVERGENCIA_ATIVA" if active else "DIVERGENTE_SEM_ESTOQUE")
        rows.append({"reference": ref, "status": status, "active_cells": active,
                     "empty_cells": empty, "unknown_cells": unknown})
    return rows


def read_stock(page, references):
    result = {}
    for ref in references:
        try:
            page.open_products()
            page.choose_prices()
            page.search(ref)
            result[ref] = page.read_stock()
        except (UnsafeState, page.read_error):
            result[ref] = {}
    return result
