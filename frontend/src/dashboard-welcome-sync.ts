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

void syncDashboardWelcome();

window.addEventListener("popstate", () => void syncDashboardWelcome());
