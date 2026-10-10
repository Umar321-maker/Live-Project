const customers = [
  { id: "7590-VHVEG", name: "Martha Graham", initials: "MG", contract: "Month-to-month", tenure: 2, charges: 70.7, internet: "Fiber optic", support: false, paperless: true, payment: "Electronic check", partner: false, color: "#efe6d6", avatar: "#766347" },
  { id: "5575-GNVDE", name: "Robert Fox", initials: "RF", contract: "One year", tenure: 29, charges: 64.8, internet: "DSL", support: true, paperless: false, payment: "Mailed check", partner: true, color: "#e0ebdd", avatar: "#48654b" },
  { id: "3668-QPYBK", name: "Eleanor Pena", initials: "EP", contract: "Month-to-month", tenure: 2, charges: 53.9, internet: "DSL", support: false, paperless: true, payment: "Mailed check", partner: false, color: "#e7e3ef", avatar: "#685b7b" },
  { id: "7795-CFOCW", name: "Cody Fisher", initials: "CF", contract: "One year", tenure: 45, charges: 42.3, internet: "DSL", support: true, paperless: false, payment: "Bank transfer", partner: true, color: "#e6e9dc", avatar: "#5e674b" },
  { id: "9237-HQITU", name: "Savannah Nguyen", initials: "SN", contract: "Month-to-month", tenure: 2, charges: 99.7, internet: "Fiber optic", support: false, paperless: true, payment: "Electronic check", partner: false, color: "#f1e3dd", avatar: "#93674e" },
  { id: "9305-CDSKC", name: "Jenny Wilson", initials: "JW", contract: "Month-to-month", tenure: 8, charges: 74.4, internet: "Fiber optic", support: false, paperless: true, payment: "Electronic check", partner: false, color: "#f3e7d5", avatar: "#8f6c3c" },
  { id: "1452-KIOVK", name: "Darlene Robertson", initials: "DR", contract: "One year", tenure: 22, charges: 89.1, internet: "Fiber optic", support: false, paperless: true, payment: "Credit card", partner: true, color: "#dce9ed", avatar: "#4c6e79" },
  { id: "6713-OKOMC", name: "Esther Howard", initials: "EH", contract: "Month-to-month", tenure: 10, charges: 29.8, internet: "No internet", support: false, paperless: false, payment: "Mailed check", partner: false, color: "#eee2eb", avatar: "#795d77" },
  { id: "7892-POOKP", name: "Cameron Williamson", initials: "CW", contract: "Month-to-month", tenure: 28, charges: 104.8, internet: "Fiber optic", support: true, paperless: true, payment: "Credit card", partner: true, color: "#e0eadd", avatar: "#4d7253" },
  { id: "6388-TABGU", name: "Leslie Alexander", initials: "LA", contract: "Two year", tenure: 43, charges: 56.2, internet: "DSL", support: true, paperless: false, payment: "Bank transfer", partner: true, color: "#e8e6d5", avatar: "#776d47" },
  { id: "9763-GRSKD", name: "Brooklyn Simmons", initials: "BS", contract: "Month-to-month", tenure: 3, charges: 74.6, internet: "Fiber optic", support: false, paperless: true, payment: "Electronic check", partner: false, color: "#e6e1f0", avatar: "#665c83" },
  { id: "7469-LKBCI", name: "Arlene McCoy", initials: "AM", contract: "Two year", tenure: 55, charges: 19.8, internet: "No internet", support: false, paperless: false, payment: "Mailed check", partner: true, color: "#f0e6dd", avatar: "#8b6c50" }
];

const churnRates = [28.4, 27.8, 28.1, 27.2, 27.6, 27.0, 26.8, 26.4, 26.8, 25.7, 25.2, 24.9];
const rows = document.getElementById("customer-rows");
const searchInput = document.getElementById("customer-search");
const riskFilter = document.getElementById("risk-filter");
const scoreDialog = document.getElementById("score-dialog");
const detailDialog = document.getElementById("detail-dialog");
let toastTimeout;

function scoreCustomer(customer) {
  let score = -1.65;
  if (customer.contract === "Month-to-month") score += 1.15;
  if (customer.contract === "One year") score -= 0.7;
  if (customer.contract === "Two year") score -= 1.2;
  score -= Math.min(customer.tenure, 72) * 0.043;
  score += Math.max(0, customer.charges - 70) * 0.025;
  if (!customer.support && customer.internet !== "No internet") score += 0.53;
  if (customer.internet === "Fiber optic") score += 0.27;
  if (customer.paperless) score += 0.13;
  if (customer.payment === "Electronic check") score += 0.37;
  if (!customer.partner) score += 0.16;
  return Math.round((1 / (1 + Math.exp(-score))) * 100);
}

function riskLevel(score) {
  if (score >= 60) return "High";
  if (score >= 35) return "Medium";
  return "Low";
}

function riskMarkup(level) {
  return `<span class="risk-badge risk-${level.toLowerCase()}">${level} risk</span>`;
}

function formatContract(contract) {
  return contract === "Month-to-month" ? "Monthly" : contract === "One year" ? "1 year" : "2 year";
}

function renderCustomers() {
  const query = searchInput.value.trim().toLowerCase();
  const selectedRisk = riskFilter.value;
  const filtered = customers
    .map((customer) => ({ ...customer, risk: scoreCustomer(customer) }))
    .filter((customer) => {
      const matchesSearch = `${customer.name} ${customer.id} ${customer.contract}`.toLowerCase().includes(query);
      return matchesSearch && (selectedRisk === "all" || riskLevel(customer.risk) === selectedRisk);
    })
    .sort((first, second) => second.risk - first.risk);

  rows.innerHTML = filtered.map((customer) => `
    <tr data-customer-id="${customer.id}" tabindex="0" aria-label="View ${customer.name} customer details">
      <td><div class="customer-cell"><span class="customer-avatar" style="background:${customer.color};color:${customer.avatar}">${customer.initials}</span><span><span class="customer-name">${customer.name}</span><span class="customer-id">${customer.id}</span></span></div></td>
      <td><span class="contract-pill">${formatContract(customer.contract)}</span></td>
      <td>${customer.tenure} months</td>
      <td>$${customer.charges.toFixed(2)}</td>
      <td>${riskMarkup(riskLevel(customer.risk))}</td>
      <td class="revenue-cell">$${(customer.charges * 12).toLocaleString("en-US", { maximumFractionDigits: 0 })}<span style="color:#92978f;font:8px var(--font)"> / yr</span></td>
      <td><button class="row-action" type="button" aria-label="View ${customer.name} details">···</button></td>
    </tr>`).join("");
  document.getElementById("table-count").textContent = filtered.length;
  document.getElementById("visible-count").textContent = filtered.length;
  document.getElementById("empty-state").hidden = filtered.length > 0;
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(toastTimeout);
  toastTimeout = window.setTimeout(() => toast.classList.remove("is-visible"), 2400);
}

function openCustomer(customer) {
  const risk = scoreCustomer(customer);
  const reasons = [];
  if (customer.contract === "Month-to-month") reasons.push("Month-to-month contract provides less commitment.");
  if (customer.tenure < 12) reasons.push("Short tenure can signal a still-forming relationship.");
  if (!customer.support && customer.internet !== "No internet") reasons.push("No tech support plan is attached to this account.");
  if (customer.payment === "Electronic check") reasons.push("Electronic check billing is associated with higher churn in this sample.");
  if (customer.charges >= 80) reasons.push("Higher monthly spend may increase price sensitivity.");
  if (!reasons.length) reasons.push("Longer tenure and a committed contract suggest a steadier account.");

  document.getElementById("detail-content").innerHTML = `
    <div class="detail-header"><div class="detail-identity"><span class="detail-avatar" style="background:${customer.color};color:${customer.avatar}">${customer.initials}</span><div><h2 class="detail-name" id="detail-name">${customer.name}</h2><div class="detail-subtitle">${customer.id} · CUSTOMER PROFILE</div></div></div><button class="detail-close" type="button" data-close-dialog aria-label="Close">×</button></div>
    <div class="detail-risk-block"><span>Illustrative churn risk</span><div class="detail-risk-value">${riskMarkup(riskLevel(risk))}<span>${risk}%</span></div></div>
    <div class="detail-facts"><div class="detail-fact"><span>Contract</span><strong>${customer.contract}</strong></div><div class="detail-fact"><span>Tenure</span><strong>${customer.tenure} months</strong></div><div class="detail-fact"><span>Monthly charges</span><strong>$${customer.charges.toFixed(2)}</strong></div><div class="detail-fact"><span>Internet</span><strong>${customer.internet}</strong></div></div>
    <div class="detail-reasons"><h3>Signals to discuss</h3><p>${reasons.map((reason) => `• ${reason}`).join("<br>")}</p></div>
    <div class="detail-actions"><button class="primary-button" type="button" data-save-customer="${customer.id}">＋ Add to save list</button><button class="secondary-button" type="button" data-score-customer="${customer.id}">Adjust score</button></div>
    <p class="disclaimer">Sample account. Score is illustrative and not a validated prediction.</p>`;
  detailDialog.showModal();
}

function drawChart() {
  const canvas = document.getElementById("churn-chart");
  const bounds = canvas.getBoundingClientRect();
  if (!bounds.width || !bounds.height) return;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(bounds.width * ratio);
  canvas.height = Math.round(bounds.height * ratio);
  const context = canvas.getContext("2d");
  context.scale(ratio, ratio);
  const width = bounds.width;
  const height = bounds.height;
  const visibleCount = Number(document.getElementById("chart-period").value);
  const data = churnRates.slice(-visibleCount);
  const min = 23;
  const max = 30;
  const left = 31;
  const right = width - 9;
  const top = 12;
  const bottom = height - 17;
  const x = (index) => left + (index / (data.length - 1)) * (right - left);
  const y = (value) => bottom - ((value - min) / (max - min)) * (bottom - top);

  context.font = '9px "DM Mono", monospace';
  context.textBaseline = "middle";
  [30, 28, 26, 24].forEach((tick) => {
    const tickY = y(tick);
    context.beginPath();
    context.setLineDash([2, 4]);
    context.strokeStyle = "#e8ebe4";
    context.lineWidth = 1;
    context.moveTo(left, tickY);
    context.lineTo(right, tickY);
    context.stroke();
    context.setLineDash([]);
    context.fillStyle = "#969c93";
    context.fillText(`${tick}%`, 1, tickY);
  });

  const averageY = y(26.5);
  context.beginPath();
  context.setLineDash([5, 4]);
  context.strokeStyle = "#d4a360";
  context.moveTo(left, averageY);
  context.lineTo(right, averageY);
  context.stroke();
  context.setLineDash([]);

  const area = context.createLinearGradient(0, top, 0, bottom);
  area.addColorStop(0, "#75ad8d42");
  area.addColorStop(1, "#75ad8d00");
  context.beginPath();
  data.forEach((value, index) => index === 0 ? context.moveTo(x(index), y(value)) : context.lineTo(x(index), y(value)));
  context.lineTo(x(data.length - 1), bottom);
  context.lineTo(x(0), bottom);
  context.closePath();
  context.fillStyle = area;
  context.fill();

  context.beginPath();
  data.forEach((value, index) => index === 0 ? context.moveTo(x(index), y(value)) : context.lineTo(x(index), y(value)));
  context.strokeStyle = "#4e9470";
  context.lineWidth = 2;
  context.lineJoin = "round";
  context.stroke();

  data.forEach((value, index) => {
    context.beginPath();
    context.arc(x(index), y(value), index === data.length - 1 ? 3.5 : 2.1, 0, Math.PI * 2);
    context.fillStyle = index === data.length - 1 ? "#4e9470" : "#fff";
    context.fill();
    context.strokeStyle = "#4e9470";
    context.lineWidth = 1.5;
    context.stroke();
  });
  context.fillStyle = "#4e9470";
  context.font = '600 9px "DM Mono", monospace';
  context.fillText(`${data[data.length - 1]}%`, Math.max(left, x(data.length - 1) - 28), y(data[data.length - 1]) - 12);
}

function calculateFormScore(form) {
  const customer = {
    contract: form.get("contract") === "month" ? "Month-to-month" : form.get("contract") === "one" ? "One year" : "Two year",
    tenure: Number(form.get("tenure")),
    charges: Number(form.get("charges")),
    internet: form.get("internet") === "none" ? "No internet" : form.get("internet"),
    support: form.get("support") === "on",
    paperless: form.get("paperless") === "on",
    payment: "Electronic check",
    partner: false
  };
  return scoreCustomer(customer);
}

rows.addEventListener("click", (event) => {
  const row = event.target.closest("tr[data-customer-id]");
  if (!row) return;
  const customer = customers.find((entry) => entry.id === row.dataset.customerId);
  if (customer) openCustomer(customer);
});
rows.addEventListener("keydown", (event) => {
  if ((event.key === "Enter" || event.key === " ") && event.target.matches("tr[data-customer-id]")) {
    event.preventDefault();
    const customer = customers.find((entry) => entry.id === event.target.dataset.customerId);
    if (customer) openCustomer(customer);
  }
});
searchInput.addEventListener("input", renderCustomers);
riskFilter.addEventListener("change", renderCustomers);
document.getElementById("chart-period").addEventListener("change", drawChart);
window.addEventListener("resize", drawChart);

document.getElementById("open-score-button").addEventListener("click", () => {
  document.getElementById("score-result").hidden = true;
  scoreDialog.showModal();
});
document.getElementById("score-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const score = calculateFormScore(form);
  const level = riskLevel(score);
  const result = document.getElementById("score-result");
  const signals = [];
  if (form.get("contract") === "month") signals.push("month-to-month contract");
  if (Number(form.get("tenure")) < 12) signals.push("short tenure");
  if (form.get("internet") === "fiber") signals.push("fiber service");
  if (form.get("support") !== "on") signals.push("no tech support");
  result.innerHTML = `<div class="result-top"><span class="result-label">Illustrative churn likelihood</span><strong class="result-score">${score}%</strong></div><div class="result-bar"><span style="width:${score}%;background:${level === "High" ? "#db765d" : level === "Medium" ? "#d0a245" : "#69a17d"}"></span></div><p class="result-factors"><strong>${level} risk.</strong> Signals considered: ${signals.join(", ") || "longer-term account signals"}. Try changing contract or tenure to explore the estimate.</p>`;
  result.hidden = false;
});

document.getElementById("detail-content").addEventListener("click", (event) => {
  const closeButton = event.target.closest("[data-close-dialog]");
  if (closeButton) detailDialog.close();
  const saveButton = event.target.closest("[data-save-customer]");
  if (saveButton) {
    saveButton.textContent = "✓ Added to save list";
    saveButton.disabled = true;
    showToast("Customer added to the retention save list.");
  }
  const scoreButton = event.target.closest("[data-score-customer]");
  if (scoreButton) {
    const customer = customers.find((entry) => entry.id === scoreButton.dataset.scoreCustomer);
    if (!customer) return;
    document.getElementById("score-form").elements.contract.value = customer.contract === "Month-to-month" ? "month" : customer.contract === "One year" ? "one" : "two";
    document.getElementById("score-form").elements.tenure.value = customer.tenure;
    document.getElementById("score-form").elements.charges.value = customer.charges;
    document.getElementById("score-form").elements.internet.value = customer.internet === "Fiber optic" ? "fiber" : customer.internet === "DSL" ? "dsl" : "none";
    document.getElementById("score-form").elements.support.checked = customer.support;
    document.getElementById("score-form").elements.paperless.checked = customer.paperless;
    detailDialog.close();
    document.getElementById("score-result").hidden = true;
    scoreDialog.showModal();
  }
});

document.querySelectorAll("[data-close-dialog]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});
document.querySelectorAll("dialog").forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
});

document.getElementById("export-button").addEventListener("click", () => {
  const header = ["customer_id", "name", "contract", "tenure_months", "monthly_charges", "illustrative_churn_risk_percent", "risk_level"];
  const lines = customers.map((customer) => [customer.id, customer.name, customer.contract, customer.tenure, customer.charges.toFixed(2), scoreCustomer(customer), riskLevel(scoreCustomer(customer))].map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","));
  const csv = [header.join(","), ...lines].join("\r\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "staysignal-sample-customer-risk.csv";
  link.click();
  URL.revokeObjectURL(url);
  showToast("Sample risk list exported as CSV.");
});

renderCustomers();
drawChart();