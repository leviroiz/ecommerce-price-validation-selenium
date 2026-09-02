"""Robot B: independently read wholesale and retail color/size matrices."""
from ..domain.prices import SIDES, UnsafeState, compare_grid


def check_xg(page, expected, emit=print):
    rows = []
    for index, (ref, target) in enumerate(expected.items(), 1):
        emit(f"[{index}/{len(expected)}] Conferindo XG {ref}")
        for side in SIDES:
            try:
                page.open_products()
                page.choose_prices()
                page.search(ref)
                actual = page.read_grid(side)
                status, cells = compare_grid(actual, target["xg"][side])
            except (UnsafeState, page.read_error):
                actual, status, cells = {}, "ERRO_LEITURA", ()
            rows.append({"reference": ref, "side": side, "status": status,
                         "divergent_cells": ";".join(cells), "count": len(cells)})
            emit(f"{side}: {status}; {len(cells)} divergentes")
    return rows
