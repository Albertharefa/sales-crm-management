import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function syncDashboardWelcome() {
  if (window.location.pathname !== "/") return;

  try {
    const response = await axios.get<{ name?: string }>(`${API_BASE_URL}/me`, {
      withCredentials: true,
    });
    const name = String(response.data?.name ?? "").trim();
    if (!name) return;

    document.documentElement.style.setProperty(
      "--dashboard-welcome",
      JSON.stringify(`Selamat Datang, ${name}!`),
    );
  } catch {
    // AppShell remains responsible for session handling; this visual sync is non-blocking.
  }
}

const navigationEvent = "crm:navigation";

const originalPushState = window.history.pushState.bind(window.history);
window.history.pushState = ((...args: Parameters<History["pushState"]>) => {
  const result = originalPushState(...args);
  window.dispatchEvent(new Event(navigationEvent));
  return result;
}) as History["pushState"];

const originalReplaceState = window.history.replaceState.bind(window.history);
window.history.replaceState = ((...args: Parameters<History["replaceState"]>) => {
  const result = originalReplaceState(...args);
  window.dispatchEvent(new Event(navigationEvent));
  return result;
}) as History["replaceState"];

const syncAfterNavigation = () => {
  window.setTimeout(() => void syncDashboardWelcome(), 0);
};

void syncDashboardWelcome();
window.addEventListener("popstate", syncAfterNavigation);
window.addEventListener(navigationEvent, syncAfterNavigation);
