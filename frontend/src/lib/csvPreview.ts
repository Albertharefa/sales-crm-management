export function openCsvPreview(url: string, title = "CSV Export Preview") {
  const previewUrl = `/csv-preview?source=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`;
  window.open(previewUrl, "_blank", "noopener,noreferrer");
}
