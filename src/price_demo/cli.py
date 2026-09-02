"""Run only the bundled local demo. Default mode never saves prices."""
import argparse
from contextlib import contextmanager
from pathlib import Path
from selenium import webdriver
from .browser.local_admin import serve
from .browser.product_page import ProductPage
from .checkers.regular_prices import check_regular
from .checkers.xg_prices import check_xg
from .checkers.stock import cross_stock, read_stock
from .correctors.xg_corrector import correct_xg
from .domain.fixtures import expected_catalog, approvals
from .domain.prices import FIELDS
from .reports.csv_report import write_csv
from .reports.journal import Journal


@contextmanager
def exclusive_run(directory):
    """OS lock released even on process interruption."""
    with (directory / ".run.lock").open("a+b") as stream:
        stream.seek(0)
        if not stream.read(1):
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        import os
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("robot", choices=("regular", "xg", "stock", "correct", "all"), nargs="?", default="all")
    parser.add_argument("--apply", action="store_true", help="Save approved synthetic corrections")
    parser.add_argument("--limit", type=int, default=245)
    parser.add_argument("--output", type=Path, default=Path("reports"))
    args = parser.parse_args()
    if not 1 <= args.limit <= 245:
        parser.error("--limit must be between 1 and 245")
    args.output.mkdir(parents=True, exist_ok=True)
    expected = dict(list(expected_catalog().items())[:args.limit])
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    with exclusive_run(args.output), serve(args.output / "state.json") as (url, _store):
        journal = Journal(args.output / "audit.sqlite")
        try:
            with webdriver.Chrome(options=options) as driver:
                page = ProductPage(driver, url)
                if args.robot in ("regular", "all"):
                    rows = check_regular(page, expected)
                    fields = ["reference", "status"]
                    for field in FIELDS:
                        fields += [field + "_expected", field + "_actual"]
                    write_csv(args.output / "regular.csv", rows, fields)
                if args.robot in ("xg", "stock", "all"):
                    rows = check_xg(page, expected)
                    write_csv(args.output / "xg.csv", rows, ["reference", "side", "status", "divergent_cells", "count"])
                    if args.robot in ("stock", "all"):
                        refs = sorted({row["reference"] for row in rows if row["status"] == "DIVERGENTE"})
                        rows = cross_stock(rows, read_stock(page, refs))
                        write_csv(args.output / "stock.csv", rows,
                                  ["reference", "status", "active_cells", "empty_cells", "unknown_cells"])
                if args.robot in ("correct", "all"):
                    rows = correct_xg(page, expected, approvals() & expected.keys(), journal, apply=args.apply)
                    write_csv(args.output / ("corrections.csv" if args.apply else "simulation.csv"),
                              rows, ["reference", "status"])
        finally:
            journal.close()


if __name__ == "__main__":
    main()
