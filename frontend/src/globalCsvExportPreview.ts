const EXPORT_PREFIX = "/api/v1/exports/";

function toAbsolutePath(value: string) {
  try { return new URL(value, window.location.origin).pathname + new URL(value, window.location.origin).search; }
  catch { return value; }
}

if (typeof window !== "undefined") {
  const originalOpen = window.open.bind(window);
  window.open = ((url?: string | URL, target?: string, features?: string) => {
    if (url) {
      const raw = String(url);
      const path = toAbsolutePath(raw);
      if (path.startsWith(EXPORT_PREFIX)) {
        const previewUrl = `/csv-preview?source=${encodeURIComponent(path)}&title=${encodeURIComponent("CSV Export Preview")}`;
        return originalOpen(previewUrl, target || "_blank", features);
      }
    }
    return originalOpen(url as string | URL | undefined, target, features);
  }) as typeof window.open;
}
