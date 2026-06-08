export function saveDownload(download) {
  if (!download?.url) {
    return;
  }

  const link = document.createElement("a");
  link.href = download.url;
  link.download = download.filename || "download";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(download.url);
}
