import argparse
import json
from selenium import webdriver
from .collector import Catalog, FIXTURE
from .executor import run
from .models import Baseline, money
from .report import Audit, single_run


def load_baselines():
    data = json.loads(FIXTURE.with_name("baseline.json").read_text(encoding="utf-8"))
    return {key: Baseline(money(v["before"]), money(v["sale"]), money(v["cost"]),
                          frozenset(tuple(pair) for pair in v["grid"]))
            for key, v in data.items()}


def main():
    parser = argparse.ArgumentParser(description="Synthetic local price validation demo")
    parser.add_argument("--apply", action="store_true", help="Save in the local mock only")
    parser.add_argument("--repeat", action="store_true", help="Reconcile twice in the same mock session")
    args = parser.parse_args()
    root = FIXTURE.parent.parent
    with single_run(root / "reports" / "run.lock"):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        with webdriver.Chrome(options=options) as driver:
            catalog = Catalog(driver)
            audit = Audit(root / "reports" / "audit.jsonl")
            for _ in range(2 if args.repeat else 1):
                results = run(catalog, load_baselines(), audit, apply=args.apply)
                print(json.dumps({"mode": "apply" if args.apply else "dry_run",
                                  "results": results}))


if __name__ == "__main__":
    main()
