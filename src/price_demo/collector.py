"""Selenium DOM adapter, restricted to one bundled local fixture."""
import json
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from .models import parse_offer

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "catalog.html"


class Catalog:
    def __init__(self, driver):
        self.driver = driver
        self.url = FIXTURE.as_uri()
        driver.get(self.url)

    def guard(self):
        if self.driver.current_url != self.url:
            raise ValueError("Only the bundled local fixture is allowed")

    def row(self, key):
        self.guard()
        rows = self.driver.find_elements(By.CSS_SELECTOR, "article[data-key]")
        matches = [r for r in rows if r.get_attribute("data-key") == key]
        if len(matches) != 1:
            raise ValueError("Missing or duplicate offer")
        return matches[0]

    def keys(self):
        self.guard()
        keys = [r.get_attribute("data-key") for r in
                self.driver.find_elements(By.CSS_SELECTOR, "article[data-key]")]
        if not keys or len(keys) != len(set(keys)):
            raise ValueError("Empty or duplicate catalog")
        return keys

    def read(self, key):
        row = self.row(key)
        return parse_offer({
            "key": key, "channel": row.get_attribute("data-channel"),
            "before": row.find_element(By.CSS_SELECTOR, ".before").text,
            "sale": row.find_element(By.CSS_SELECTOR, ".saved-sale").text,
            "source": row.get_attribute("data-source"),
            "variants": json.loads(row.find_element(By.CSS_SELECTOR, ".grid").text),
        })

    def write(self, key, target):
        row = self.row(key)
        field = row.find_element(By.CSS_SELECTOR, "input")
        field.clear()
        field.send_keys(str(target))
        row.find_element(By.CSS_SELECTOR, "button").click()
        WebDriverWait(self.driver, 3).until(lambda _: self.read(key).sale == target)

    def refresh(self):
        self.guard()
        self.driver.refresh()
