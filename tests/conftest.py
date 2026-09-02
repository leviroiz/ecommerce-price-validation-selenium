from copy import deepcopy
import pytest
from price_demo.domain.fixtures import expected_catalog, initial_catalog
from price_demo.domain.prices import UnsafeState


class FakePage:
    read_error = RuntimeError

    def __init__(self):
        self.data = initial_catalog()
        for product in self.data.values():
            product["revision"] = 0
        self.ref = None
        self.writes = 0
        self.selected = True
        self.fail = None

    def open_products(self):
        self.ref = None

    def choose_prices(self):
        pass

    def search(self, ref):
        if ref not in self.data:
            raise UnsafeState("Missing reference")
        self.ref = ref

    def read_regular(self):
        return deepcopy(self.data[self.ref]["regular"])

    def read_grid(self, side):
        return deepcopy(self.data[self.ref]["xg"][side])

    def read_stock(self):
        return deepcopy(self.data[self.ref]["stock"])

    def snapshot(self):
        return deepcopy({key: self.data[self.ref][key] for key in ("regular", "xg", "stock", "revision")})

    def open_batch(self):
        if self.fail == "batch":
            raise UnsafeState("Batch unavailable")

    def prepare(self, ref, before, target):
        if not self.selected:
            raise UnsafeState("Selection uncertain")

    def save(self, ref, before, target):
        if self.fail == "before":
            raise RuntimeError("Interrupted before save")
        self.data[ref]["xg"] = deepcopy(target["xg"])
        self.data[ref]["revision"] += 1
        self.writes += 1
        if self.fail == "after":
            raise RuntimeError("Interrupted after save")
        if self.fail == "post":
            self.data[ref]["xg"]["atacado"]["Ciano|T1"] = "99.00"

    def reload(self):
        pass


@pytest.fixture
def fake():
    return FakePage()


@pytest.fixture
def expected():
    return expected_catalog()
