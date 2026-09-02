"""Real Chrome, local HTTP, real DOM; scripts below only inject test faults."""
from copy import deepcopy
import pytest
from selenium import webdriver
from price_demo.browser.local_admin import serve
from price_demo.browser.product_page import ProductPage
from price_demo.checkers.regular_prices import check_regular
from price_demo.checkers.xg_prices import check_xg
from price_demo.checkers.stock import cross_stock, read_stock
from price_demo.correctors.xg_corrector import correct_xg
from price_demo.domain.prices import UnsafeState
from price_demo.reports.journal import Journal

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    with webdriver.Chrome(options=options) as browser:
        yield browser


@pytest.fixture
def admin(driver, tmp_path):
    with serve(tmp_path / "state.json") as (url, store):
        yield ProductPage(driver, url), store


def test_full_245_regular_and_xg_dom(admin, expected):
    page, store = admin
    before = deepcopy(store.data)
    regular = check_regular(page, expected, lambda _: None)
    assert len(regular) == 245
    assert sum(row["status"] == "OK" for row in regular) == 243
    assert regular[4]["status"] == "DIVERGENTE"
    assert regular[5]["status"] == "ERRO_LEITURA"
    for field, value in expected["DEMO-006"]["regular"].items():
        assert regular[5][field + "_actual"] == ("ilegivel" if field == "wholesale_sale" else value)
        assert regular[5][field + "_read_status"] == ("ILEGIVEL" if field == "wholesale_sale" else "LIDO")
    xg = check_xg(page, expected, lambda _: None)
    assert len(xg) == 490
    assert sum(row["status"] == "DIVERGENTE" for row in xg) == 5
    assert sum(row["status"] == "SEM_VALORES" for row in xg) == 2
    assert sum(row["status"] == "ERRO_LEITURA" for row in xg) == 1
    refs = {row["reference"] for row in xg if row["status"] == "DIVERGENTE"}
    stock = cross_stock(xg, read_stock(page, refs))
    assert next(row for row in stock if row["reference"] == "DEMO-003")["status"] == "DIVERGENTE_SEM_ESTOQUE"
    assert store.data == before


def test_apply_and_restart_browser_server(admin, expected, tmp_path, driver):
    page, store = admin
    path = tmp_path / "audit.sqlite"
    journal = Journal(path)
    approved = {"DEMO-002", "DEMO-007"}
    try:
        untouched = deepcopy(store.data["DEMO-003"])
        rows = correct_xg(page, expected, approved, journal, emit=lambda _: None)
        assert [row["status"] for row in rows] == ["SIMULADO"] * 2
        assert store.data["DEMO-002"]["revision"] == 0
        correct_xg(page, expected, approved, journal, apply=True, emit=lambda _: None)
        assert store.data["DEMO-003"] == untouched
    finally:
        journal.close()
    # Fresh HTTP server and browser session read the same durable state.
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    with serve(store.path) as (url, restarted), webdriver.Chrome(options=options) as new_driver:
        resumed = ProductPage(new_driver, url)
        journal = Journal(path)
        try:
            rows = correct_xg(resumed, expected, approved, journal, apply=True, emit=lambda _: None)
            assert [row["status"] for row in rows] == ["JA_CORRETO"] * 2
            assert restarted.data["DEMO-002"]["revision"] == 1
            assert restarted.data["DEMO-007"]["revision"] == 1
            assert journal.db.execute("SELECT COUNT(*) FROM operations").fetchone()[0] == 2
        finally:
            journal.close()


def selected(page):
    page.open_products()
    page.choose_prices()
    page.search("DEMO-002")


@pytest.mark.parametrize("fault", ["duplicate-card", "duplicate-field", "duplicate-cell", "missing-cell"])
def test_ambiguous_dom_blocks(admin, fault):
    page, store = admin
    selected(page)
    selectors = {"duplicate-card": "article", "duplicate-field": "[data-demo-field]",
                 "duplicate-cell": "[data-demo-cell]", "missing-cell": "[data-demo-cell]"}
    script = ("document.querySelector(arguments[0]).remove();" if fault == "missing-cell" else
              "const x=document.querySelector(arguments[0]);x.after(x.cloneNode(true));")
    page.driver.execute_script(script, selectors[fault])
    if fault == "missing-cell":
        from price_demo.domain.prices import compare_grid
        with pytest.raises(UnsafeState):
            compare_grid(page.read_grid("atacado"), store.expected["DEMO-002"]["xg"]["atacado"])
    else:
        with pytest.raises(UnsafeState):
            page.snapshot()
    assert store.data["DEMO-002"]["revision"] == 0


@pytest.mark.parametrize("fault", ["unchecked", "extra-selection", "wrong-form", "wrong-target", "disabled-save"])
def test_batch_fail_safe(admin, fault):
    page, store = admin
    selected(page)
    before = page.snapshot()
    target = deepcopy(before)
    target["xg"] = store.expected["DEMO-002"]["xg"]
    page.open_batch()
    page.prepare("DEMO-002", before, target)
    scripts = {
        "unchecked": "document.querySelector('[data-demo-select]').checked=false;",
        "extra-selection": "const e=document.querySelector('[data-demo-select]');e.after(e.cloneNode(true));",
        "wrong-form": "document.querySelector('#demo-batch-form').dataset.demoReference='DEMO-003';",
        "wrong-target": "document.querySelector('#demo-batch-form input').value='90.00';",
        "disabled-save": "document.querySelector('#demo-save').disabled=true;",
    }
    page.driver.execute_script(scripts[fault])
    with pytest.raises(UnsafeState):
        page.save("DEMO-002", before, target)
    assert store.data["DEMO-002"]["revision"] == 0


def test_server_rejects_stale_state(admin):
    page, store = admin
    selected(page)
    before = page.snapshot()
    target = deepcopy(before)
    target["xg"] = store.expected["DEMO-002"]["xg"]
    page.open_batch()
    page.prepare("DEMO-002", before, target)
    store.data["DEMO-002"]["revision"] += 1
    with pytest.raises(UnsafeState, match="not confirmed"):
        page.save("DEMO-002", before, target)
    assert store.data["DEMO-002"]["xg"] == before["xg"]


def test_browser_left_fixture(admin):
    page, _store = admin
    page.driver.get("about:blank")
    with pytest.raises(UnsafeState):
        page.open_products()


def test_interruption_after_real_save_recovers(admin, expected, tmp_path, monkeypatch):
    page, store = admin
    path = tmp_path / "journal.sqlite"
    journal = Journal(path)
    original = page.save
    def interrupted(*args):
        original(*args)
        raise RuntimeError("Interrupted after actual HTTP save")
    monkeypatch.setattr(page, "save", interrupted)
    try:
        with pytest.raises(RuntimeError):
            correct_xg(page, expected, {"DEMO-002"}, journal, True, lambda _: None)
        assert store.data["DEMO-002"]["revision"] == 1
    finally:
        journal.close()
    monkeypatch.setattr(page, "save", original)
    page.reload()
    journal = Journal(path)
    try:
        changed = deepcopy(expected)
        changed["DEMO-002"]["xg"]["atacado"]["Ciano|T1"] = "55.55"
        with pytest.raises(UnsafeState, match="different target; manual review"):
            correct_xg(page, changed, {"DEMO-002"}, journal, True, lambda _: None)
        assert store.data["DEMO-002"]["revision"] == 1
        assert journal.db.execute("SELECT status FROM operations").fetchall() == [("pending",)]
        result = correct_xg(page, expected, {"DEMO-002"}, journal, True, lambda _: None)
        assert result[0]["status"] == "JA_CORRETO"
        assert store.data["DEMO-002"]["revision"] == 1
        assert journal.db.execute("SELECT status FROM operations").fetchone()[0] == "verified"
    finally:
        journal.close()


def test_post_write_readback_failure_stops(admin, expected, tmp_path, monkeypatch):
    page, store = admin
    journal = Journal(tmp_path / "audit.sqlite")
    original = page.reload
    def corrupt_after_save():
        store.data["DEMO-002"]["xg"]["varejo"]["Ciano|T1"] = "88.00"
        original()
    monkeypatch.setattr(page, "reload", corrupt_after_save)
    try:
        with pytest.raises(UnsafeState, match="Post-write"):
            correct_xg(page, expected, {"DEMO-002", "DEMO-007"}, journal, True, lambda _: None)
        assert store.data["DEMO-007"]["revision"] == 0
        assert journal.db.execute("SELECT status FROM operations").fetchone()[0] == "pending"
    finally:
        journal.close()
