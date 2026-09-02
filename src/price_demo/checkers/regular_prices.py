"""Robot A: read four prices per reference, with isolated read failures."""
from ..domain.prices import UnsafeState, compare_regular, money


def check_regular(page, expected, emit=print):
    rows = []
    for index, (ref, target) in enumerate(expected.items(), 1):
        emit(f"[{index}/{len(expected)}] Conferindo {ref}")
        values = {}
        try:
            page.open_products()
            page.choose_prices()
            page.search(ref)
            values = page.read_regular()
            status = compare_regular(values, target["regular"])
        except (UnsafeState, page.read_error):
            status = "ERRO_LEITURA"
        row = {"reference": ref, "status": status}
        for field, value in target["regular"].items():
            row[field + "_expected"] = value
            row[field + "_actual"] = values.get(field, "")
            if field not in values:
                read_status = "NAO_LIDO"
            else:
                try:
                    read_status = "VAZIO" if money(values[field]) is None else "LIDO"
                except UnsafeState:
                    read_status = "ILEGIVEL"
            row[field + "_read_status"] = read_status
        rows.append(row)
        emit(status)
    return rows
