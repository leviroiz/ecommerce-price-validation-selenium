from dataclasses import replace
import json
import pytest
from price_demo.executor import run
from price_demo.models import Baseline, Offer, Variant, money
from price_demo.report import Audit, single_run


class FakeCatalog:
    def __init__(self):
        self.offer = Offer('SYN-001-retail','retail',money('120.00'),money('110.00'),
                           'synthetic_api_drift',(Variant('blue','XG',2),))
        self.writes = 0

    def keys(self):
        return [self.offer.key]

    def read(self, key):
        return self.offer

    def write(self, key, target):
        self.writes += 1
        self.offer = replace(self.offer, sale=target)

    def refresh(self):
        pass


@pytest.fixture
def setup(tmp_path):
    catalog = FakeCatalog()
    baseline = Baseline(money('120.00'), money('100.00'), money('60.00'), frozenset({('blue','XG')}))
    return catalog, {catalog.offer.key:baseline}, Audit(tmp_path / 'audit.jsonl')


def test_dry_run_and_idempotent_resume(setup):
    catalog, baselines, audit = setup
    assert run(catalog, baselines, audit) == ['correct']
    assert catalog.writes == 0
    run(catalog, baselines, audit, apply=True)
    assert run(catalog, baselines, audit, apply=True) == ['unchanged']
    assert catalog.writes == 1
    records = [json.loads(line) for line in audit.path.read_text().splitlines()]
    assert [r['status'] for r in records].count('verified') == 1


def test_crash_after_save_reconciles_without_second_write(setup):
    catalog, baselines, audit = setup
    original = catalog.write
    def interrupted(key, target):
        original(key, target)
        raise RuntimeError('simulated interruption after save')
    catalog.write = interrupted
    with pytest.raises(RuntimeError):
        run(catalog, baselines, audit, apply=True)
    catalog.write = original
    assert run(catalog, baselines, audit, apply=True) == ['unchanged']
    assert catalog.writes == 1


def test_failed_persistence_is_not_success(setup):
    catalog, baselines, audit = setup
    initial = catalog.offer
    catalog.refresh = lambda: setattr(catalog, 'offer', initial)
    with pytest.raises(RuntimeError, match='Post-write'):
        run(catalog, baselines, audit, apply=True)
    assert '"status": "verified"' not in audit.path.read_text()


def test_concurrent_change_prevents_write(setup):
    catalog, baselines, audit = setup
    count = 0
    def changing_read(key):
        nonlocal count
        count += 1
        return catalog.offer if count == 1 else replace(catalog.offer, source='manual')
    catalog.read = changing_read
    with pytest.raises(RuntimeError, match='State changed'):
        run(catalog, baselines, audit, apply=True)
    assert catalog.writes == 0


def test_audit_failure_prevents_write(setup):
    catalog, baselines, audit = setup
    def unavailable(**event):
        raise OSError('audit unavailable')
    audit.record = unavailable
    with pytest.raises(OSError):
        run(catalog, baselines, audit, apply=True)
    assert catalog.writes == 0


def test_single_execution_lock(tmp_path):
    path = tmp_path / 'run.lock'
    with single_run(path):
        with pytest.raises(FileExistsError):
            with single_run(path):
                pytest.fail('must not acquire twice')
    assert not path.exists()
