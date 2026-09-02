from decimal import Decimal
import pytest
from price_demo.domain.prices import money, reference, regular, compare_grid, UnsafeState
from price_demo.checkers.stock import cross_stock
from price_demo.checkers.regular_prices import check_regular
from price_demo.checkers.xg_prices import check_xg
from price_demo.domain.fixtures import approvals


@pytest.mark.parametrize("text,value", [("12.34", Decimal("12.34")), ("12,34", Decimal("12.34")), ("", None), (None, None)])
def test_money(text, value):
    assert money(text) == value


@pytest.mark.parametrize("text", ["NaN", "Infinity", "-3.00", "0.00", "1", "1.234", "1,234.00", "=1+2", "x", 1])
def test_bad_price(text):
    with pytest.raises(UnsafeState):
        money(text)


@pytest.mark.parametrize("ref", ["", "DEMO-1", "REAL-001", "DEMO-001x", "=DEMO-001", None])
def test_bad_reference(ref):
    with pytest.raises(UnsafeState):
        reference(ref)


def test_four_fields_required():
    with pytest.raises(UnsafeState):
        regular({"wholesale_sale": "10.00"})


@pytest.mark.parametrize("actual,status,cells", [
    ({"a": "10.00", "b": "10.00"}, "OK", ()),
    ({"a": "11.00", "b": "10.00"}, "DIVERGENTE", ("a",)),
    ({"a": None, "b": None}, "SEM_VALORES", ()),
    ({"a": None, "b": "10.00"}, "DIVERGENTE", ("a",)),
])
def test_grid(actual, status, cells):
    assert compare_grid(actual, {"a": "10.00", "b": "10.00"}) == (status, cells)


@pytest.mark.parametrize("actual", [{}, {"a": "10.00"}, {"a": "x", "b": "10.00"}])
def test_grid_failure(actual):
    with pytest.raises(UnsafeState):
        compare_grid(actual, {"a": "10.00", "b": "10.00"})


def test_full_regular_fixture(fake, expected):
    messages = []
    rows = check_regular(fake, expected, messages.append)
    assert len(rows) == 245
    assert [row["status"] for row in rows].count("OK") == 243
    assert rows[4]["status"] == "DIVERGENTE"
    assert rows[5]["status"] == "ERRO_LEITURA"
    assert "[12/245] Conferindo DEMO-012" in messages


def test_sides_are_independent(fake, expected):
    rows = check_xg(fake, expected, lambda _: None)
    by_key = {(row["reference"], row["side"]): row for row in rows}
    assert len(rows) == 490
    assert by_key["DEMO-002", "atacado"]["status"] == "DIVERGENTE"
    assert by_key["DEMO-002", "varejo"]["status"] == "OK"
    assert by_key["DEMO-004", "atacado"]["status"] == "SEM_VALORES"
    assert by_key["DEMO-009", "varejo"]["status"] == "ERRO_LEITURA"


@pytest.mark.parametrize("quantity,status", [(0, "DIVERGENTE_SEM_ESTOQUE"), (1, "DIVERGENCIA_ATIVA"),
    (None, "ERRO_LEITURA"), (-1, "ERRO_LEITURA"), ("3", "ERRO_LEITURA"), (True, "ERRO_LEITURA")])
def test_stock_exact_variant(quantity, status):
    rows = [{"reference": "DEMO-001", "status": "DIVERGENTE", "divergent_cells": "Ciano|T1"}]
    result = cross_stock(rows, {"DEMO-001": {"Ciano|T1": quantity, "Ambar|T1": 500}})
    assert result[0]["status"] == status


def test_stock_deduplicates_sides():
    rows = [{"reference": "DEMO-001", "status": "DIVERGENTE", "divergent_cells": "Ciano|T1"}] * 2
    assert cross_stock(rows, {"DEMO-001": {"Ciano|T1": 2}})[0]["active_cells"] == 1


def test_approval_not_derived_from_stock():
    assert approvals() == {"DEMO-002", "DEMO-007"}


def test_unreadable_other_side_does_not_claim_stock_clear():
    rows = [{"reference": "DEMO-001", "status": "DIVERGENTE", "divergent_cells": "Ciano|T1"},
            {"reference": "DEMO-001", "status": "ERRO_LEITURA", "divergent_cells": ""}]
    assert cross_stock(rows, {"DEMO-001": {"Ciano|T1": 0}})[0]["status"] == "ERRO_LEITURA"


def test_read_failure_does_not_abort_remaining(fake, expected):
    del fake.data["DEMO-001"]
    assert check_regular(fake, dict(list(expected.items())[:2]), lambda _: None)[1]["status"] == "OK"
