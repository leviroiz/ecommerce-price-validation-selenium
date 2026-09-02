"""Robot D: approved references only, seven steps, compare-and-save."""
from copy import deepcopy
from ..domain.prices import SIDES, UnsafeState, regular, compare_grid, same_prices
from ..reports.journal import fingerprint

STEPS = ("abrindo Gerenciar Produtos", "selecionando Precos",
         "pesquisando e selecionando a referencia", "validando os quatro campos de preco",
         "abrindo Alterar Precos em Lote", "conferindo selecao e preparando",
         "salvando")


def correct_xg(page, expected, approved, journal, apply=False, emit=print):
    if not set(approved) <= expected.keys():
        raise UnsafeState("Approval references absent from expected fixture")
    results = []
    for index, ref in enumerate(sorted(approved), 1):
        emit(f"[{index}/{len(approved)}] Corrigindo grade {ref}")
        def step(number):
            emit(f"Etapa {number}/7: {STEPS[number - 1]}")
        step(1)
        page.open_products()
        step(2)
        page.choose_prices()
        step(3)
        page.search(ref)
        step(4)
        before = page.snapshot()
        target = deepcopy(before)
        target["xg"] = deepcopy(expected[ref]["xg"])
        if regular(before["regular"]) != regular(expected[ref]["regular"]):
            raise UnsafeState("Four regular prices do not match expected values")
        for side in SIDES:
            status, _ = compare_grid(before["xg"][side], target["xg"][side])
            if status == "SEM_VALORES":
                raise UnsafeState("Empty XG side requires manual review")
        key = fingerprint({"reference": ref, "regular": target["regular"], "xg": target["xg"]})
        if journal.has_conflicting_pending(ref, key):
            raise UnsafeState("Pending operation has a different target; manual review required")
        previous = journal.get(key)
        if previous:
            old, intended, state = previous
            if same_prices(before, intended):
                if before["stock"] != old["stock"] or before["revision"] != old["revision"] + 1:
                    raise UnsafeState("Recovery found changed stock or revision; manual review required")
                if apply:
                    journal.verified(key)
                results.append({"reference": ref, "status": "JA_CORRETO"})
                emit("JA_CORRETO")
                continue
            if state == "verified" or before != old:
                raise UnsafeState("State changed since journal intent; manual review required")
        if same_prices(before, target):
            results.append({"reference": ref, "status": "JA_CORRETO"})
            emit("JA_CORRETO")
            continue
        step(5)
        page.open_batch()
        step(6)
        page.prepare(ref, before, target)
        if not apply:
            results.append({"reference": ref, "status": "SIMULADO"})
            emit("SIMULADO: nenhuma escrita")
            continue
        if not previous:
            journal.pending(key, ref, before, target)
        step(7)
        page.save(ref, before, target)
        # Reopen the persisted product, not just the form's optimistic values.
        page.reload()
        page.open_products()
        page.choose_prices()
        page.search(ref)
        verified = page.snapshot()
        if (not same_prices(verified, target) or verified["stock"] != before["stock"]
                or verified["revision"] != before["revision"] + 1):
            raise UnsafeState("Post-write verification failed; stop the entire run")
        journal.verified(key)
        results.append({"reference": ref, "status": "CORRIGIDO"})
        emit("OK")
    return results
