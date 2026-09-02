"""Real DOM integration: no mocked WebDriver and no external website."""
from decimal import Decimal
import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from price_demo.collector import Catalog
from price_demo.cli import load_baselines
from price_demo.executor import run
from price_demo.report import Audit

pytestmark = pytest.mark.browser


@pytest.fixture
def catalog():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-dev-shm-usage')
    with webdriver.Chrome(options=options) as driver:
        yield Catalog(driver)


def test_real_dom_dry_run_apply_refresh_resume(catalog, tmp_path):
    audit = Audit(tmp_path / 'audit.jsonl')
    baseline = load_baselines()
    initial = {key: catalog.read(key) for key in catalog.keys()}
    assert run(catalog, baseline, audit) == ['correct','correct','unchanged','blocked','blocked','blocked']
    assert {key: catalog.read(key) for key in catalog.keys()} == initial
    run(catalog, baseline, audit, apply=True)
    assert catalog.read('SYN-001-retail').sale == Decimal('100.00')
    assert catalog.read('SYN-001-wholesale').sale == Decimal('80.00')
    assert run(catalog, baseline, audit, apply=True) == ['unchanged','unchanged','unchanged','blocked','blocked','blocked']
    for key in list(initial)[2:]:
        assert catalog.read(key) == initial[key]


def test_dom_guard_and_duplicate_identity(catalog):
    catalog.driver.execute_script("const row=document.querySelector('article');row.after(row.cloneNode(true));")
    with pytest.raises(ValueError, match='duplicate'):
        catalog.keys()
    catalog.driver.get('about:blank')
    with pytest.raises(ValueError, match='local fixture'):
        catalog.keys()


def test_save_failure_stops_and_audits(catalog, tmp_path):
    catalog.driver.execute_script("document.querySelector('button').disabled=true;")
    audit = Audit(tmp_path / 'audit.jsonl')
    with pytest.raises(TimeoutException):
        run(catalog, load_baselines(), audit, apply=True)
    assert '"status": "intent"' in audit.path.read_text()
    assert '"status": "verified"' not in audit.path.read_text()
    assert '"status": "failed"' in audit.path.read_text()
