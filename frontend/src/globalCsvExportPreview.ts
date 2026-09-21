const isCsvExportPath = (path: string) => {
  const pathname = path.split("?")[0];
  return pathname.startsWith("/api/v1/exports/") || pathname.includes("/export") || pathname.includes("/exports/");
};

function toAbsolutePath(value: string) {
  try {
    const url = new URL(value, window.location.origin);
    return `${url.pathname}${url.search}`;
  } catch {
    return value;
  }
}

if (typeof window !== "undefined") {
  const originalOpen = window.open.bind(window);

  window.open = ((url?: string | URL, target?: string, features?: string) => {
    if (url) {
      const path = toAbsolutePath(String(url));
      if (isCsvExportPath(path)) {
        const previewUrl = `/csv-preview?source=${encodeURIComponent(path)}&title=${encodeURIComponent("CSV Export Preview")}`;
        return originalOpen(previewUrl, target || "_blank", features);
      }
    }
    return originalOpen(url as string | URL | undefined, target, features);
  }) as typeof window.open;
}
