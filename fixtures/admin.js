"use strict";
let current = null;
const byId = id => document.getElementById(id);
const clone = value => JSON.parse(JSON.stringify(value));
const fields = ["wholesale_list", "wholesale_sale", "retail_list", "retail_sale"];
const labels = ["Atacado de", "Atacado por", "Varejo de", "Varejo por"];
function node(tag, attrs = {}, text = "") {
  const item = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) item.setAttribute(key, value);
  item.textContent = text;
  return item;
}
byId("demo-products").onclick = () => {
  byId("demo-workspace").hidden = false;
  byId("demo-search-area").hidden = true;
  byId("demo-result").replaceChildren();
  current = null;
};
byId("demo-prices").onclick = () => {byId("demo-search-area").hidden = false;};
byId("demo-search").onclick = async () => {
  byId("demo-search-state").textContent = "BUSCANDO";
  byId("demo-result").replaceChildren();
  current = null;
  try {
    const response = await fetch("catalog");
    if (!response.ok) throw new Error("read");
    const products = await response.json();
    const ref = byId("demo-query").value;
    if (!Object.hasOwn(products, ref)) {
      byId("demo-search-state").textContent = "AUSENTE";
      return;
    }
    current = clone(products[ref]);
    render();
    byId("demo-search-state").textContent = "PRONTO";
  } catch (_) {byId("demo-search-state").textContent = "ERRO";}
};
function gridTable(values, side, batch = false) {
  const table = node("table", {"data-demo-side": side, "data-demo-kind": batch ? "batch" : "grid"});
  const head = node("tr");
  for (const label of ["Cor", "Tamanho", "Preco"]) head.append(node("th", {}, label));
  table.append(head);
  for (const [key, value] of Object.entries(values)) {
    const row = node("tr");
    const [color, size] = key.split("|");
    row.append(node("td", {}, color), node("td", {}, size));
    const cell = node("td");
    cell.append(node("input", {"data-demo-cell": key, value: value ?? "", ...(batch ? {} : {readonly: ""})}));
    row.append(cell);
    table.append(row);
  }
  return table;
}
function render() {
  const card = node("article", {"data-demo-reference": current.reference, "data-demo-revision": current.revision});
  card.append(node("h2", {}, current.name));
  const selection = node("input", {type: "checkbox", "data-demo-select": current.reference});
  const selectLabel = node("label", {}, "Selecionar apenas esta referencia");
  selectLabel.prepend(selection);
  card.append(selectLabel);
  const normal = node("fieldset", {id: "demo-regular"});
  normal.append(node("legend", {}, "Quatro campos conceituais"));
  fields.forEach((field, i) => {
    const label = node("label", {}, labels[i]);
    label.append(node("input", {"data-demo-field": field, value: current.regular[field] ?? "", readonly: ""}));
    normal.append(label);
  });
  card.append(normal);
  for (const side of ["atacado", "varejo"]) {
    const button = node("button", {"data-demo-tab": side}, "Precos XG " + side);
    const table = gridTable(current.xg[side], side);
    table.hidden = true;
    button.onclick = () => {
      card.querySelectorAll('table[data-demo-kind="grid"]').forEach(item => {item.hidden = true;});
      table.hidden = false;
    };
    card.append(button, table);
  }
  const inventory = node("div", {id: "demo-stock"});
  for (const [key, value] of Object.entries(current.stock)) {
    inventory.append(node("span", {"data-demo-stock": key, "data-demo-quantity": value}, key + ": " + value + " "));
  }
  card.append(inventory);
  const batch = node("button", {id: "demo-batch"}, "Alterar Precos em Lote");
  batch.onclick = () => openBatch(card);
  card.append(batch);
  byId("demo-result").replaceChildren(card);
}
function openBatch(card) {
  card.querySelector("#demo-batch-form")?.remove();
  const form = node("fieldset", {id: "demo-batch-form", "data-demo-reference": current.reference});
  form.append(node("legend", {}, "Conferir selecao e preparar valores absolutos"));
  for (const side of ["atacado", "varejo"]) form.append(gridTable(current.xg[side], side, true));
  const save = node("button", {id: "demo-save"}, "Salvar");
  const status = node("p", {id: "demo-save-state", role: "status"});
  save.onclick = async () => {
    status.textContent = "SALVANDO";
    save.disabled = true;
    const xg = {};
    for (const side of ["atacado", "varejo"]) {
      xg[side] = {};
      form.querySelectorAll('table[data-demo-side="' + side + '"] input').forEach(input => {
        xg[side][input.dataset.demoCell] = input.value || null;
      });
    }
    const before = {};
    for (const key of ["regular", "xg", "stock", "revision"]) before[key] = current[key];
    const selection = [...document.querySelectorAll("[data-demo-select]:checked")].map(input => input.dataset.demoSelect);
    try {
      const response = await fetch("save", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({reference: current.reference, selection, before, xg})
      });
      status.textContent = response.ok ? "SALVO" : "BLOQUEADO";
    } catch (_) {status.textContent = "INCERTO";}
  };
  form.append(save, status);
  card.append(form);
}
