from dataclasses import replace
from decimal import Decimal as D
import pytest
from price_demo.models import Baseline, Offer, Variant, money, parse_offer
from price_demo.rules import decide


@pytest.fixture
def baseline():
    return Baseline(D('120.00'), D('100.00'), D('60.00'), frozenset({('blue', 'M'), ('blue', 'XG')}))


@pytest.fixture
def offer():
    return Offer('SYN-001-retail', 'retail', D('120.00'), D('110.00'), 'synthetic_api_drift',
                 (Variant('blue', 'M', 4), Variant('blue', 'XG', 2)))


@pytest.mark.parametrize('price,action', [('100.00','unchanged'), ('100.01','unchanged'),
    ('99.99','unchanged'), ('100.02','correct'), ('99.98','correct')])
def test_cent_boundary(offer, baseline, price, action):
    assert decide(replace(offer, sale=D(price)), baseline).action == action


def test_selective_repair_and_stock_exposure(offer, baseline):
    result = decide(offer, baseline)
    assert result.action == 'correct'
    assert result.unit_delta == D('-10.00')
    assert result.stock_exposure == D('-60.00')


@pytest.mark.parametrize('change,reason', [
    ({'before': D('121.00')}, 'de_changed'),
    ({'sale': D('121.00')}, 'inverted_de_por'),
    ({'sale': D('0.00')}, 'invalid_amount'),
    ({'sale': D('NaN')}, 'invalid_amount'),
    ({'sale': D('Infinity')}, 'invalid_amount'),
    ({'source': 'manual'}, 'unconfirmed_cause'),
    ({'variants': (Variant('blue','M',4),)}, 'uncertain_grid'),
    ({'variants': (Variant('blue','M',4),Variant('red','XG',2))}, 'uncertain_grid'),
    ({'variants': (Variant('blue','M',4),Variant('blue','XG',2),Variant('blue','XG',2))}, 'uncertain_grid'),
    ({'variants': (Variant('blue','M',4),Variant('blue','XG',0))}, 'no_sellable_xg_stock'),
    ({'variants': (Variant('blue','M',0),Variant('blue','XG',0))}, 'no_sellable_xg_stock'),
    ({'variants': (Variant('blue','M',4),Variant('blue','XG',-1))}, 'invalid_stock'),
    ({'sale': D('74.99')}, 'change_exceeds_demo_limit'),
])
def test_uncertainty_blocks(offer, baseline, change, reason):
    decision = decide(replace(offer, **change), baseline)
    assert (decision.action, decision.reason) == ('blocked', reason)


def test_margin_and_missing_baseline(offer, baseline):
    assert decide(offer, None).reason == 'missing_baseline'
    assert decide(offer, replace(baseline, cost=D('90.01'))).reason == 'margin_below_demo_limit'
    assert decide(offer, replace(baseline, cost=D('90.00'))).action == 'correct'
    assert decide(replace(offer, sale=D('75.00')), baseline).action == 'correct'


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-1.00', '1.001', '1,00', 'R$ 1,00', '', '1e2'])
def test_strict_money(value):
    with pytest.raises(ValueError):
        money(value)


def test_parser_rejects_ambiguous_stock():
    with pytest.raises(ValueError):
        parse_offer({'key':'SYN-001-retail','channel':'retail','before':'120.00', 'sale':'110.00',
                     'source':'unknown','variants':[{'color':'blue','size':'XG','stock':'2.5'}]})
