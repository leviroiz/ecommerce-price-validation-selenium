"""Selenium DOM only. Selectors are original and exclusive to this fixture."""
from urllib.parse import urlsplit
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from ..domain.prices import FIELDS, SIDES, UnsafeState, reference


class ProductPage:
    read_error = WebDriverException

    def __init__(self, driver, url):
        parsed = urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port:
            raise UnsafeState("Only the loopback synthetic admin is supported")
        self.driver, self.url, self.ref = driver, url, None
        driver.get(url)

    def guard(self):
        if self.driver.current_url != self.url:
            raise UnsafeState("Browser left the allowed synthetic page")

    def elements(self, selector, scope=None):
        self.guard()
        return (scope or self.driver).find_elements(By.CSS_SELECTOR, selector)

    def one(self, selector, scope=None):
        elements = self.elements(selector, scope)
        if len(elements) != 1:
            raise UnsafeState("Missing or ambiguous DOM element")
        return elements[0]

    def click(self, selector):
        element = self.one(selector)
        if not element.is_displayed() or not element.is_enabled():
            raise UnsafeState("Control unavailable")
        element.click()

    def open_products(self):
        self.click("#demo-products")
        self.ref = None

    def choose_prices(self):
        self.click("#demo-prices")

    def search(self, ref):
        reference(ref)
        field = self.one("#demo-query")
        field.clear()
        field.send_keys(ref)
        self.click("#demo-search")
        WebDriverWait(self.driver, 5, poll_frequency=0.05).until(
            lambda _: self.one("#demo-search-state").text in ("PRONTO", "AUSENTE", "ERRO"))
        self.ref = ref
        self.card()

    def card(self):
        card = self.one("article[data-demo-reference]")
        if card.get_attribute("data-demo-reference") != self.ref or not card.is_displayed():
            raise UnsafeState("Unexpected product identity")
        return card

    def read_regular(self):
        card = self.card()
        inputs = self.elements("#demo-regular input[data-demo-field]", card)
        values = {item.get_attribute("data-demo-field"): item.get_attribute("value") or None for item in inputs}
        if len(inputs) != 4 or set(values) != set(FIELDS):
            raise UnsafeState("Four unique regular fields required")
        return values

    def read_grid(self, side):
        if side not in SIDES:
            raise UnsafeState("Unknown price side")
        self.card()
        self.click(f'[data-demo-tab="{side}"]')
        table = self.one(f'table[data-demo-kind="grid"][data-demo-side="{side}"]')
        if not table.is_displayed():
            raise UnsafeState("Grid not visible")
        return self.grid_values(table)

    def grid_values(self, table):
        inputs = self.elements("input[data-demo-cell]", table)
        values = {item.get_attribute("data-demo-cell"): item.get_attribute("value") or None for item in inputs}
        if not inputs or len(values) != len(inputs):
            raise UnsafeState("Missing or duplicated color/size cell")
        return values

    def read_stock(self):
        self.card()
        elements = self.elements("[data-demo-stock]")
        result = {}
        for item in elements:
            key, value = item.get_attribute("data-demo-stock"), item.get_attribute("data-demo-quantity")
            if key in result or not value or not value.isdigit():
                raise UnsafeState("Unknown or duplicate stock")
            result[key] = int(value)
        return result

    def snapshot(self):
        return {"regular": self.read_regular(), "xg": {side: self.read_grid(side) for side in SIDES},
                "stock": self.read_stock(), "revision": int(self.card().get_attribute("data-demo-revision"))}

    def open_batch(self):
        self.card()
        box = self.one("[data-demo-select]")
        if box.get_attribute("data-demo-select") != self.ref:
            raise UnsafeState("Incorrect selection identity")
        if not box.is_selected():
            box.click()
        self.click("#demo-batch")

    def validate_selection(self, ref):
        self.card()
        boxes = self.elements("[data-demo-select]")
        if len(boxes) != 1 or not boxes[0].is_selected() or boxes[0].get_attribute("data-demo-select") != ref:
            raise UnsafeState("Uncertain batch selection")
        form = self.one("#demo-batch-form")
        if form.get_attribute("data-demo-reference") != ref or not form.is_displayed():
            raise UnsafeState("Wrong batch form")

    def prepare(self, ref, before, target):
        self.validate_selection(ref)
        if self.snapshot() != before:
            raise UnsafeState("State changed during preparation")
        for side in SIDES:
            table = self.one(f'table[data-demo-kind="batch"][data-demo-side="{side}"]')
            if self.grid_values(table).keys() != target["xg"][side].keys():
                raise UnsafeState("Batch topology differs")
            for element in self.elements("input[data-demo-cell]", table):
                element.clear()
                value = target["xg"][side][element.get_attribute("data-demo-cell")]
                if value is not None:
                    element.send_keys(value)

    def save(self, ref, before, target):
        self.validate_selection(ref)
        if self.snapshot() != before:
            raise UnsafeState("State changed before saving")
        for side in SIDES:
            table = self.one(f'table[data-demo-kind="batch"][data-demo-side="{side}"]')
            if self.grid_values(table) != target["xg"][side]:
                raise UnsafeState("Prepared values differ from expected")
        self.click("#demo-save")
        WebDriverWait(self.driver, 5, poll_frequency=0.05).until(
            lambda _: self.one("#demo-save-state").text in ("SALVO", "BLOQUEADO", "INCERTO"))
        if self.one("#demo-save-state").text != "SALVO":
            raise UnsafeState("Save not confirmed")

    def reload(self):
        self.guard()
        self.driver.refresh()
        self.ref = None
