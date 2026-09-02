from copy import deepcopy
import pytest
from price_demo.correctors.xg_corrector import correct_xg
from price_demo.domain.prices import UnsafeState
from price_demo.reports.journal import Journal
from price_demo.reports.csv_report import write_csv, safe_cell
from price_demo.cli import exclusive_run


@pytest.fixture
def journal(tmp_path):
    result = Journal(tmp_path / "audit.sqlite")
    yield result
    result.close()


def run(fake, expected, journal, **kwargs):
    return correct_xg(fake, expected, {"DEMO-002", "DEMO-007"}, journal, emit=lambda _: None, **kwargs)


def test_simulation_does_not_write(fake, expected, journal):
    before = deepcopy(fake.data)
    assert len(run(fake, expected, journal)) == 2
    assert fake.data == before
    assert journal.db.execute("SELECT COUNT(*) FROM operations").fetchone()[0] == 0


def test_selective_and_idempotent(fake, expected, journal):
    untouched = deepcopy(fake.data["DEMO-003"])
    messages = []
    rows = correct_xg(fake, expected, {"DEMO-002", "DEMO-007"}, journal, True, messages.append)
    assert [row["status"] for row in rows] == ["CORRIGIDO", "CORRIGIDO"]
    assert all(any(f"Etapa {n}/7" in message for message in messages) for n in range(1, 8))
    assert [row["status"] for row in run(fake, expected, journal, apply=True)] == ["JA_CORRETO"] * 2
    assert fake.writes == 2 and fake.data["DEMO-003"] == untouched
    assert journal.db.execute("SELECT COUNT(*) FROM operations").fetchone()[0] == 2


@pytest.mark.parametrize("point", ["before", "after"])
def test_resume_interruption(fake, expected, tmp_path, point):
    path = tmp_path / "audit.sqlite"
    first = Journal(path)
    fake.fail = point
    with pytest.raises(RuntimeError):
        run(fake, expected, first, apply=True)
    first.close()
    fake.fail = None
    second = Journal(path)
    try:
        run(fake, expected, second, apply=True)
        assert fake.writes == 2
        assert second.db.execute("SELECT COUNT(*) FROM operations WHERE status='verified'").fetchone()[0] == 2
    finally:
        second.close()


@pytest.mark.parametrize("mode", ["batch", "post"])
def test_failure_stops_whole_run(fake, expected, journal, mode):
    fake.fail = mode
    with pytest.raises(UnsafeState):
        run(fake, expected, journal, apply=True)
    assert fake.data["DEMO-007"]["revision"] == 0


def test_selection_fail_safe(fake, expected, journal):
    fake.selected = False
    with pytest.raises(UnsafeState):
        run(fake, expected, journal, apply=True)
    assert fake.writes == 0


@pytest.mark.parametrize("ref", ["DEMO-004", "DEMO-005", "DEMO-006", "DEMO-009"])
def test_bad_state_blocks(fake, expected, journal, ref):
    with pytest.raises(UnsafeState):
        correct_xg(fake, expected, {ref}, journal, True, lambda _: None)
    assert fake.writes == 0


def test_unknown_approval(fake, expected, journal):
    with pytest.raises(UnsafeState):
        correct_xg(fake, expected, {"DEMO-999"}, journal, True)
    assert fake.writes == 0


def test_drift_after_verified_blocks(fake, expected, journal):
    run(fake, expected, journal, apply=True)
    fake.data["DEMO-002"]["xg"]["atacado"]["Ciano|T1"] = "44.00"
    with pytest.raises(UnsafeState):
        run(fake, expected, journal, apply=True)
    assert fake.writes == 2


def test_pending_drift_blocks(fake, expected, journal):
    fake.fail = "before"
    with pytest.raises(RuntimeError):
        run(fake, expected, journal, apply=True)
    fake.fail = None
    fake.data["DEMO-002"]["stock"]["Ciano|T1"] = 12
    with pytest.raises(UnsafeState):
        run(fake, expected, journal, apply=True)
    assert fake.writes == 0


@pytest.mark.parametrize("change", ["stock", "revision"])
def test_recovery_checks_non_price_state(fake, expected, journal, change):
    fake.fail = "after"
    with pytest.raises(RuntimeError):
        run(fake, expected, journal, apply=True)
    fake.fail = None
    if change == "stock":
        fake.data["DEMO-002"]["stock"]["Ciano|T1"] += 1
    else:
        fake.data["DEMO-002"]["revision"] += 1
    with pytest.raises(UnsafeState):
        run(fake, expected, journal, apply=True)
    assert fake.writes == 1


def test_reports_replace_not_append(tmp_path):
    path = tmp_path / "report.csv"
    rows = [{"reference": "DEMO-001", "status": "OK"}]
    write_csv(path, rows, ["reference", "status"])
    before = path.read_bytes()
    write_csv(path, rows, ["reference", "status"])
    assert path.read_bytes() == before
    with pytest.raises(ValueError):
        write_csv(path, rows * 2, ["reference", "status"])
    assert path.read_bytes() == before


@pytest.mark.parametrize("value", ["=1+1", "+SUM(A1)", "-1", "@A1", "  =2"])
def test_csv_formula_escape(value):
    assert safe_cell(value).startswith("'")


def test_run_lock_released(tmp_path):
    with exclusive_run(tmp_path):
        with pytest.raises(OSError):
            with exclusive_run(tmp_path):
                pass
    with exclusive_run(tmp_path):
        pass
