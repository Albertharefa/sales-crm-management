const updateDashboardGreeting = () => {
  if (window.location.pathname !== "/") return;

  const heading = document.querySelector<HTMLElement>('[data-testid="dashboard-page"] > div:first-child h1');
  const userName = document.querySelector<HTMLElement>('[data-testid="header-user-name"]')?.textContent?.trim();

  if (!heading || !userName) return;

  heading.textContent = `Selamat Datang, ${userName}!`;
};

const observer = new MutationObserver(() => updateDashboardGreeting());
observer.observe(document.documentElement, { childList: true, subtree: true });

window.addEventListener("popstate", updateDashboardGreeting);
window.addEventListener("hashchange", updateDashboardGreeting);
window.setTimeout(updateDashboardGreeting, 0);
window.setTimeout(updateDashboardGreeting, 250);
window.setTimeout(updateDashboardGreeting, 1000);
