const syncPipelineAnalytics = () => {
  if (window.location.pathname !== "/pipeline") return;

  const root = document.querySelector<HTMLElement>(".crm-pipeline-analytics");
  if (!root) return;

  const loading = Array.from(document.querySelectorAll<HTMLElement>("[data-testid=\"pipeline-page\"] *"))
    .some((element) => element.textContent?.trim() === "Memuat Sales Pipeline...");

  root.style.visibility = loading ? "hidden" : "visible";
};

const observer = new MutationObserver(() => syncPipelineAnalytics());
observer.observe(document.body, { childList: true, subtree: true });

window.setTimeout(syncPipelineAnalytics, 0);
window.setTimeout(syncPipelineAnalytics, 100);
window.setTimeout(syncPipelineAnalytics, 250);
window.setTimeout(syncPipelineAnalytics, 500);
window.setTimeout(syncPipelineAnalytics, 1000);
