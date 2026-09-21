import { queryClient } from "@/lib/queryClient";

const compactMoney = (value: number) => new Intl.NumberFormat("id-ID", { style:"currency", currency:"IDR", notation:"compact", maximumFractionDigits:1 }).format(Number(value)||0).replace("IDR","Rp");

const injectStyles = () => {
  if (document.getElementById("dashboard-business-performance-style")) return;
  const style = document.createElement("style"); style.id="dashboard-business-performance-style";
  style.textContent=`
    [data-testid="dashboard-page"] .dashboard-business-performance-hero{position:relative!important;min-width:0!important;min-height:136px!important;padding:18px 26px!important;overflow:hidden!important;box-sizing:border-box!important;border-radius:16px!important;background:linear-gradient(115deg,#173b78 0%,#1f4f98 52%,#285fa8 100%)!important;border:1px solid rgba(37,99,235,.28)!important;box-shadow:0 7px 20px rgba(15,23,42,.16)!important}
    [data-testid="dashboard-page"] .dashboard-business-performance-metrics{position:absolute;right:18px;top:50%;transform:translateY(-50%);z-index:4;display:grid;grid-template-columns:170px 185px 170px;gap:6px;width:537px}
    [data-testid="dashboard-page"] .dashboard-business-performance-card{min-width:0!important;width:100%!important;height:72px!important;padding:8px 10px!important;box-sizing:border-box;border:1px solid rgba(255,255,255,.9);border-radius:9px;background:rgba(255,255,255,.96);box-shadow:0 2px 7px rgba(15,23,42,.12);color:#0f172a;backdrop-filter:blur(6px);display:flex;flex-direction:column;justify-content:center}
    [data-testid="dashboard-page"] .dashboard-business-performance-card span{display:block;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-size:9px;font-weight:700;letter-spacing:.07em;line-height:1.15;color:#64748b}
    [data-testid="dashboard-page"] .dashboard-business-performance-card strong{display:block;margin-top:6px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-size:18px;line-height:1;font-weight:750;letter-spacing:-.02em}
    [data-testid="dashboard-page"] .dashboard-business-performance-percentage{background:rgba(239,246,255,.98);border-color:rgba(147,197,253,.85)}
    [data-testid="dashboard-page"] .dashboard-business-performance-percentage strong{color:#2563eb}
    [data-testid="dashboard-page"] .crm-summary-grid > * > div:nth-child(3),[data-testid="dashboard-page"] .crm-summary-grid > * > div:nth-child(3) *{border:0!important;outline:0!important;box-shadow:none!important}
    [data-testid="dashboard-page"] .crm-summary-grid > * > div:nth-child(3)::before,[data-testid="dashboard-page"] .crm-summary-grid > * > div:nth-child(3)::after,[data-testid="dashboard-page"] .crm-summary-grid > * > div:nth-child(3) *::before,[data-testid="dashboard-page"] .crm-summary-grid > * > div:nth-child(3) *::after{content:none!important;display:none!important}
    @media(min-width:1200px){[data-testid="dashboard-page"] .dashboard-business-performance-hero>h2,[data-testid="dashboard-page"] .dashboard-business-performance-hero>p,[data-testid="dashboard-page"] .dashboard-business-performance-hero>div:first-child{max-width:calc(100% - 570px)!important}}
    @media(max-width:1199px){[data-testid="dashboard-page"] .dashboard-business-performance-metrics{position:relative;right:auto;top:auto;transform:none;grid-template-columns:repeat(3,minmax(0,1fr));width:100%;margin:8px 0 0 auto}[data-testid="dashboard-page"] .dashboard-business-performance-card{width:100%!important;height:68px!important}[data-testid="dashboard-page"] .dashboard-business-performance-hero{min-height:170px!important}}
    @media(max-width:767px){[data-testid="dashboard-page"] .dashboard-business-performance-metrics{grid-template-columns:1fr;width:100%}[data-testid="dashboard-page"] .dashboard-business-performance-card{width:100%!important;height:58px!important;padding:8px 10px!important}[data-testid="dashboard-page"] .dashboard-business-performance-card strong{font-size:16px;margin-top:5px}[data-testid="dashboard-page"] .dashboard-business-performance-card span{font-size:9px}[data-testid="dashboard-page"] .dashboard-business-performance-hero{min-height:0!important;padding:16px!important}}
  `; document.head.appendChild(style);
};

const findHero=()=>Array.from(document.querySelectorAll<HTMLElement>('[data-testid="dashboard-page"] section')).find(section=>section.querySelector("h2")?.textContent?.trim()==="Business performance at a glance");

const renderMetrics = (data: any) => {
  if (window.location.pathname !== "/") return;
  const hero = findHero();
  if (!hero || !data) return;

  hero.classList.add("dashboard-business-performance-hero");
  injectStyles();

  const target = Number(data?.sales_target) || 0;
  const achievement = Number(data?.po_value) || 0;
  const percentage = target > 0 ? (achievement / target) * 100 : 0;

  let metrics = hero.querySelector<HTMLElement>(".dashboard-business-performance-metrics");
  if (!metrics) {
    metrics = document.createElement("div");
    metrics.className = "dashboard-business-performance-metrics";
    metrics.innerHTML = `
      <div class="dashboard-business-performance-card dashboard-business-performance-target"><span>TARGET</span><strong></strong></div>
      <div class="dashboard-business-performance-card dashboard-business-performance-achievement"><span>PENCAPAIAN</span><strong></strong></div>
      <div class="dashboard-business-performance-card dashboard-business-performance-percentage"><span>PENCAPAIAN %</span><strong></strong></div>`;
    hero.appendChild(metrics);
  }

  const targetValue = metrics.querySelector<HTMLElement>(".dashboard-business-performance-target strong");
  const achievementValue = metrics.querySelector<HTMLElement>(".dashboard-business-performance-achievement strong");
  const percentageValue = metrics.querySelector<HTMLElement>(".dashboard-business-performance-percentage strong");
  if (targetValue) targetValue.textContent = compactMoney(target);
  if (achievementValue) achievementValue.textContent = compactMoney(achievement);
  if (percentageValue) percentageValue.textContent = `${percentage.toFixed(2)}%`;
};

const scheduleRender = (data: any) => {
  requestAnimationFrame(() => renderMetrics(data));
};

const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
  const query = event?.query;
  if (!query || !Array.isArray(query.queryKey) || query.queryKey[0] !== "dashboard") return;
  const data = query.state.data;
  if (!data) return;
  scheduleRender(data);
});

// Keep the subscription alive for SPA navigation; no DOM observer or polling is used.
void unsubscribe;
