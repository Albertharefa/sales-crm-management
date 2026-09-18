const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const compactMoney = (value: number) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(Number(value) || 0).replace("IDR", "Rp");

const injectStyles = () => {
  if (document.getElementById("dashboard-business-performance-style")) return;
  const style = document.createElement("style");
  style.id = "dashboard-business-performance-style";
  style.textContent = `
    [data-testid="dashboard-page"] .dashboard-business-performance-hero {
      position: relative !important;
      min-width: 0 !important;
      min-height: 172px !important;
      padding: 28px 34px !important;
      overflow: hidden !important;
      box-sizing: border-box !important;
      border-radius: 20px !important;
    }
    [data-testid="dashboard-page"] .dashboard-business-performance-metrics {
      position: absolute;
      right: 28px;
      top: 50%;
      bottom: auto;
      transform: translateY(-50%);
      z-index: 4;
      display: grid;
      grid-template-columns: repeat(3, minmax(112px, 1fr));
      gap: 8px;
      width: min(372px, 40%);
    }
    [data-testid="dashboard-page"] .dashboard-business-performance-card {
      min-width: 0;
      height: 64px;
      padding: 9px 11px;
      box-sizing: border-box;
      border: 1px solid rgba(255,255,255,.58);
      border-radius: 10px;
      background: rgba(255,255,255,.94);
      box-shadow: 0 3px 10px rgba(15,23,42,.07);
      color: #0f172a;
      backdrop-filter: blur(8px);
    }
    [data-testid="dashboard-page"] .dashboard-business-performance-card span {
      display: block;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      font-size: 9px;
      font-weight: 700;
      letter-spacing: .1em;
      color: #64748b;
    }
    [data-testid="dashboard-page"] .dashboard-business-performance-card strong {
      display: block;
      margin-top: 6px;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      font-size: 16px;
      line-height: 1;
      font-weight: 750;
      letter-spacing: -.02em;
    }
    [data-testid="dashboard-page"] .dashboard-business-performance-percentage {
      background: rgba(239,246,255,.96);
      border-color: rgba(96,165,250,.5);
    }
    [data-testid="dashboard-page"] .dashboard-business-performance-percentage strong { color: #2563eb; }
    @media (min-width: 1200px) {
      [data-testid="dashboard-page"] .dashboard-business-performance-hero > h2,
      [data-testid="dashboard-page"] .dashboard-business-performance-hero > p,
      [data-testid="dashboard-page"] .dashboard-business-performance-hero > div:first-child {
        max-width: calc(100% - 405px) !important;
      }
    }
    @media (max-width: 1199px) {
      [data-testid="dashboard-page"] .dashboard-business-performance-metrics {
        position: relative;
        right: auto;
        top: auto;
        bottom: auto;
        transform: none;
        width: min(100%, 520px);
        margin: 12px 0 0 auto;
      }
      [data-testid="dashboard-page"] .dashboard-business-performance-hero {
        min-height: 190px !important;
      }
    }
    @media (max-width: 767px) {
      [data-testid="dashboard-page"] .dashboard-business-performance-metrics {
        grid-template-columns: 1fr;
        width: 100%;
      }
      [data-testid="dashboard-page"] .dashboard-business-performance-card { height: 60px; }
      [data-testid="dashboard-page"] .dashboard-business-performance-hero {
        min-height: 0 !important;
        padding: 22px !important;
      }
    }
  `;
  document.head.appendChild(style);
};

const findHero = () =>
  Array.from(document.querySelectorAll<HTMLElement>('[data-testid="dashboard-page"] section')).find(
    (section) => section.querySelector("h2")?.textContent?.trim() === "Business performance at a glance",
  );

const ensureMetrics = async () => {
  if (window.location.pathname !== "/") return;

  const hero = findHero();
  if (!hero || hero.querySelector(".dashboard-business-performance-metrics")) return;
  hero.classList.add("dashboard-business-performance-hero");
  injectStyles();

  try {
    const response = await fetch(`${API_BASE_URL}/dashboard?client_version=20260912`, {
      credentials: "include",
    });
    if (!response.ok) return;

    const data = await response.json();
    const target = Number(data?.sales_target) || 0;
    const achievement = Number(data?.target_achievement) || 0;

    const achievementForPercentage =
      target >= 1_000_000_000 && achievement > 0 && achievement < 1_000_000_000
        ? achievement * 1_000_000
        : achievement;
    const percentage = target > 0 ? (achievementForPercentage / target) * 100 : 0;

    const metrics = document.createElement("div");
    metrics.className = "dashboard-business-performance-metrics";
    metrics.innerHTML = `
      <div class="dashboard-business-performance-card dashboard-business-performance-target">
        <span>TARGET</span>
        <strong>${compactMoney(target)}</strong>
      </div>
      <div class="dashboard-business-performance-card dashboard-business-performance-achievement">
        <span>PENCAPAIAN</span>
        <strong>${compactMoney(achievement)}</strong>
      </div>
      <div class="dashboard-business-performance-card dashboard-business-performance-percentage">
        <span>PENCAPAIAN %</span>
        <strong>${percentage.toFixed(2)}%</strong>
      </div>
    `;

    hero.appendChild(metrics);
  } catch {
    // Dashboard remains usable if the auxiliary performance request fails.
  }
};

const boot = () => void ensureMetrics();

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot, { once: true });
} else {
  boot();
}

const observer = new MutationObserver(() => {
  if (findHero()) {
    void ensureMetrics();
    observer.disconnect();
  }
});
observer.observe(document.body, { childList: true, subtree: true });
