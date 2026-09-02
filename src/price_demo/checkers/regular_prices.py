"""Robot A: read four prices per reference, with isolated read failures."""
from ..domain.prices import UnsafeState, compare_regular


def check_regular(page, expected, emit=print):
    rows = []
    for index, (ref, target) in enumerate(expected.items(), 1):
        emit(f"[{index}/{len(expected)}] Conferindo {ref}")
        try:
            page.open_products()
            page.choose_prices()
            page.search(ref)
            values = page.read_regular()
            status = compare_regular(values, target["regular"])
        except (UnsafeState, page.read_error):
            values, status = {}, "ERRO_LEITURA"
        row = {"reference": ref, "status": status}
        for field, value in target["regular"].items():
            row[field + "_expected"] = value
            row[field + "_actual"] = values.get(field, "")
        rows.append(row)
        emit(status)
    return rows
