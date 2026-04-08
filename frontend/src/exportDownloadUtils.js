import { API_URL } from "./apiBase";

export function downloadBlobAsFile(blob, filename) {
  const url = globalThis.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  globalThis.URL.revokeObjectURL(url);
  a.remove();
}

export async function refreshUserExportsSidebar(
  setUserExports,
  setUserExportsLoading,
  setUserExportsError,
  consoleWarnMessage,
) {
  setUserExportsLoading(true);
  try {
    const res = await fetch(`${API_URL}/api/user_exports`);
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    const data = await res.json();
    setUserExports(data);
    setUserExportsLoading(false);
  } catch (err) {
    console.warn(consoleWarnMessage, err);
    setUserExportsError("فشل في تحميل ملفات قام المستخدم بحفظها");
    setUserExportsLoading(false);
  }
}
