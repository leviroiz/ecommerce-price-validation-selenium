from copy import deepcopy
import pytest
from price_demo.browser.local_admin import Store
from price_demo.domain.prices import UnsafeState


@pytest.mark.parametrize("fault", ["selection", "revision", "target", "regular"])
def test_server_write_guards(tmp_path, fault):
    store = Store(tmp_path / "state.json")
    ref = "DEMO-002"
    old = store.data[ref]
    before = deepcopy({key: old[key] for key in ("regular", "xg", "stock", "revision")})
    payload = {"reference": ref, "selection": [ref], "before": before,
               "xg": deepcopy(store.expected[ref]["xg"])}
    if fault == "selection":
        payload["selection"].append("DEMO-003")
    elif fault == "revision":
        payload["before"]["revision"] = 999
    elif fault == "target":
        payload["xg"]["atacado"]["Ciano|T1"] = "99.00"
    else:
        store.data[ref]["regular"]["retail_sale"] = "80.00"
    with pytest.raises(UnsafeState):
        store.save(payload)
    assert store.data[ref]["revision"] == 0


def test_store_durable_and_rejects_replay(tmp_path):
    path = tmp_path / "state.json"
    store = Store(path)
    ref = "DEMO-002"
    before = deepcopy({key: store.data[ref][key] for key in ("regular", "xg", "stock", "revision")})
    payload = {"reference": ref, "selection": [ref], "before": before, "xg": store.expected[ref]["xg"]}
    store.save(payload)
    restarted = Store(path)
    assert restarted.data[ref]["revision"] == 1
    with pytest.raises(UnsafeState):
        restarted.save(payload)
