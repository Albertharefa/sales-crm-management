const STAGES = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"];
const COLORS = ["#2563eb", "#38bdf8", "#7c3aed", "#f59e0b", "#10b981", "#ef4444"];

const money = (value: number) => new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  notation: "compact",
  maximumFractionDigits: 1,
}).format(value);

const escapeHtml = (value: unknown) => String(value ?? "")
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/\"/g, "&quot;")
  .replace(/'/g, "&#039;");

type Opportunity = {
  stage?: string;
  value?: number;
  probability?: number;
  sales_name?: string | null;
};

type PipelineResponse = { items?: Opportunity[] };

let renderTimer: number | undefined;
let refreshTimer: number | undefined;
let observer: MutationObserver | undefined;

const scheduleRender = () => {
  window.clearTimeout(renderTimer);
  renderTimer = window.setTimeout(() => {
    if (window.location.pathname !== "/pipeline") return;
    void renderAnalytics();
  }, 180);
};

const fetchPipeline = async (): Promise<Opportunity[]> => {
  const response = await fetch("/api/v1/pipeline?page=1&page_size=5000", {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`Pipeline analytics HTTP ${response.status}`);
  const data = await response.json() as PipelineResponse;
  return Array.isArray(data.items) ? data.items : [];
};

const buildDonut = (stageValues: number[], total: number) => {
  if (!total) return "conic-gradient(#e2e8f0 0 100%)";
  let cursor = 0;
  const parts = stageValues.map((value, index) => {
    const start = cursor;
    cursor += (value / total) * 100;
    return `${COLORS[index]} ${start.toFixed(2)}% ${cursor.toFixed(2)}%`;
  });
  return `conic-gradient(${parts.join(", ")})`;
};

const renderAnalytics = async () => {
  if (window.location.pathname !== "/pipeline") return;
  const summary = document.querySelector<HTMLElement>(".crm-summary-grid");
  if (!summary) return;

  let root = document.querySelector<HTMLElement>(".crm-pipeline-analytics");
  if (!root) {
    root = document.createElement("section");
    root.className = "crm-pipeline-analytics";
    summary.insertAdjacentElement("afterend", root);
  }

  root.classList.add("is-loading");
  try {
    const items = await fetchPipeline();
    const stageData = STAGES.map((name, index) => {
      const rows = items.filter((item) => item.stage === name);
      const value = rows.reduce((sum, item) => sum + Number(item.value || 0), 0);
      const weighted = rows.reduce((sum, item) => sum + Number(item.value || 0) * Number(item.probability || 0) / 100, 0);
      return { name, color: COLORS[index], count: rows.length, value, weighted };
    });

    const open = stageData.filter((item) => !["Won", "Lost"].includes(item.name));
    const won = stageData.find((item) => item.name === "Won")?.value ?? 0;
    const lost = stageData.find((item) => item.name === "Lost")?.value ?? 0;
    const openValue = open.reduce((sum, item) => sum + item.value, 0);
    const weighted = open.reduce((sum, item) => sum + item.weighted, 0);
    const totalValue = stageData.reduce((sum, item) => sum + item.value, 0);
    const totalDeals = items.length;
    const winRate = totalValue > 0 ? (won / totalValue) * 100 : 0;
    const coverage = openValue > 0 ? (weighted / openValue) * 100 : 0;
    const maxValue = Math.max(...stageData.map((item) => item.value), 1);
    const donut = buildDonut(stageData.map((item) => item.value), totalValue);

    root.innerHTML = `
      <div class="crm-pipeline-analytics-head">
        <div>
          <div class="crm-pipeline-eyebrow">PIPELINE ANALYTICS</div>
          <h3>Pipeline value &amp; weighted coverage</h3>
          <p>Live calculation from current Opportunity data</p>
        </div>
        <div class="crm-pipeline-live"><span></span> LIVE DATA</div>
      </div>
      <div class="crm-pipeline-analytics-grid">
        <div class="crm-pipeline-stage-chart">
          ${stageData.map((item) => `
            <div class="crm-stage-row">
              <div class="crm-stage-meta">
                <span class="crm-stage-dot" style="background:${item.color}"></span>
                <span class="crm-stage-name">${escapeHtml(item.name)}</span>
                <span class="crm-stage-count">${item.count} deal${item.count === 1 ? "" : "s"}</span>
                <strong>${money(item.value)}</strong>
              </div>
              <div class="crm-stage-track">
                <span class="crm-stage-value-bar" style="width:${Math.max(2, (item.value / maxValue) * 100)}%;background:${item.color}"></span>
                <span class="crm-stage-weighted-bar" style="width:${Math.max(1, (item.weighted / maxValue) * 100)}%"></span>
              </div>
              <div class="crm-stage-weighted">Weighted <b>${money(item.weighted)}</b></div>
            </div>
          `).join("")}
        </div>
        <div class="crm-pipeline-insight-card">
          <div class="crm-donut-wrap">
            <div class="crm-pipeline-donut" style="background:${donut}"><div><b>${totalDeals}</b><span>DEALS</span></div></div>
          </div>
          <div class="crm-pipeline-insights">
            <div><span>Weighted coverage</span><b>${coverage.toFixed(1)}%</b></div>
            <div><span>Won / total value</span><b>${winRate.toFixed(1)}%</b></div>
            <div><span>Won value</span><b>${money(won)}</b></div>
            <div><span>Lost value</span><b>${money(lost)}</b></div>
          </div>
        </div>
      </div>
      <div class="crm-pipeline-analytics-footer">
        <span>Open <b>${money(openValue)}</b></span>
        <span>Weighted <b>${money(weighted)}</b></span>
        <span>Won <b>${money(won)}</b></span>
      </div>
    `;
  } catch {
    root.innerHTML = `
      <div class="crm-pipeline-analytics-error">
        <b>Pipeline Analytics</b><span>Data analytics belum dapat dimuat. Pipeline utama tetap berjalan normal.</span>
      </div>
    `;
  } finally {
    root.classList.remove("is-loading");
  }
};

const start = () => {
  const isPipeline = window.location.pathname === "/pipeline";
  if (!isPipeline) {
    document.querySelector(".crm-pipeline-analytics")?.remove();
    if (observer) observer.disconnect();
    observer = undefined;
    if (refreshTimer) window.clearInterval(refreshTimer);
    refreshTimer = undefined;
    return;
  }

  if (!observer) {
    observer = new MutationObserver(() => scheduleRender());
    observer.observe(document.body, { childList: true, subtree: true });
  }

  scheduleRender();
  if (!refreshTimer) {
    refreshTimer = window.setInterval(() => {
      if (window.location.pathname === "/pipeline") void renderAnalytics();
    }, 15000);
  }
};

document.addEventListener("change", (event) => {
  if (window.location.pathname !== "/pipeline") return;
  const target = event.target as HTMLElement | null;
  if (target?.closest("table")) window.setTimeout(() => void renderAnalytics(), 250);
});

window.addEventListener("popstate", start);
window.addEventListener("hashchange", start);

const bootObserver = new MutationObserver(start);
bootObserver.observe(document.body, { childList: true, subtree: true });
start();
