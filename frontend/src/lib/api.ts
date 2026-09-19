import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

let pendingGetRequests = 0;
let loadingTimer: number | undefined;

function ensureGlobalLoadingOverlay() {
  if (typeof document === 'undefined') return;
  if (document.getElementById('crm-global-data-loading')) return;

  const overlay = document.createElement('div');
  overlay.id = 'crm-global-data-loading';
  overlay.setAttribute('role', 'status');
  overlay.setAttribute('aria-live', 'polite');
  overlay.style.cssText = [
    'position:fixed',
    'inset:0',
    'z-index:99999',
    'display:flex',
    'align-items:center',
    'justify-content:center',
    'background:rgba(248,250,252,.78)',
    'backdrop-filter:blur(2px)',
    'pointer-events:auto',
  ].join(';');
  overlay.innerHTML = '<div style="display:flex;align-items:center;gap:12px;padding:12px 18px;border:1px solid #e2e8f0;border-radius:12px;background:#fff;box-shadow:0 8px 30px rgba(15,23,42,.12);font:600 14px/1.2 Arial,sans-serif;color:#334155"><span style="width:18px;height:18px;border:2px solid #cbd5e1;border-top-color:#2563eb;border-radius:50%;animation:crmGlobalSpin .7s linear infinite"></span><span>Memuat data CRM...</span></div>';

  if (!document.getElementById('crm-global-data-loading-style')) {
    const style = document.createElement('style');
    style.id = 'crm-global-data-loading-style';
    style.textContent = '@keyframes crmGlobalSpin{to{transform:rotate(360deg)}}';
    document.head.appendChild(style);
  }

  document.body.appendChild(overlay);
}

function beginGlobalGetLoading() {
  if (typeof window === 'undefined' || window.location.pathname === '/login') return;
  pendingGetRequests += 1;
  if (loadingTimer !== undefined) window.clearTimeout(loadingTimer);
  loadingTimer = window.setTimeout(() => {
    if (pendingGetRequests > 0) ensureGlobalLoadingOverlay();
  }, 80);
}

function endGlobalGetLoading() {
  if (pendingGetRequests > 0) pendingGetRequests -= 1;
  if (pendingGetRequests !== 0 || typeof document === 'undefined') return;
  if (loadingTimer !== undefined && typeof window !== 'undefined') {
    window.clearTimeout(loadingTimer);
    loadingTimer = undefined;
  }
  document.getElementById('crm-global-data-loading')?.remove();
}

api.interceptors.request.use(
  config => {
    if (String(config.method ?? 'get').toLowerCase() === 'get') beginGlobalGetLoading();
    return config;
  },
  error => Promise.reject(error),
);

api.interceptors.response.use(
  response => {
    if (String(response.config.method ?? 'get').toLowerCase() === 'get') endGlobalGetLoading();
    return response;
  },
  error => {
    if (String(error?.config?.method ?? 'get').toLowerCase() === 'get') endGlobalGetLoading();
    if (error?.response?.status === 401 && window.location.pathname !== '/login') {
      window.location.assign('/login');
    }
    return Promise.reject(error);
  },
);

function normalizeCustomerCustomValues(url: string, data: unknown): unknown {
  // Customer -> Tambah Customer -> Lainnya uses a visible manual input.
  // Read the DOM value at submit time as a final guard so the manually
  // entered value cannot be lost if the controlled UI state is stale.
  if (url !== '/customers' || typeof document === 'undefined' || !data || typeof data !== 'object') {
    return data;
  }

  const payload = { ...(data as Record<string, unknown>) };

  const industryInput = document.querySelector<HTMLInputElement>(
    '[data-testid="customer-industry-other-input"]',
  );
  const sourceInput = document.querySelector<HTMLInputElement>(
    '[data-testid="customer-source-other-input"]',
  );

  const industryOther = industryInput?.value?.trim() || '';
  const sourceOther = sourceInput?.value?.trim() || '';

  if (payload.industry === 'Lainnya' && industryOther) {
    payload.industry = industryOther;
  }

  if (payload.source === 'Lainnya' && sourceOther) {
    payload.source = sourceOther;
  }

  return payload;
}

export const apiGet = <T>(url: string) => api.get<T>(url).then(r => r.data);
export const apiPost = <T>(url: string, data?: unknown) =>
  api.post<T>(url, normalizeCustomerCustomValues(url, data)).then(r => r.data);
export const apiPut = <T>(url: string, data?: unknown) => api.put<T>(url, data).then(r => r.data);
export const apiPatch = <T>(url: string, data?: unknown) => api.patch<T>(url, data).then(r => r.data);
export const apiDelete = <T = unknown>(url: string) => api.delete<T>(url).then(r => r.data);

export const apiUpload = <T>(url: string, file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post<T>(url, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};

export type ApiStreamEvent = {
  type: 'meta' | 'delta' | 'done' | 'error';
  conversation_id?: string;
  assistant_message_id?: string;
  model?: string;
  content?: string;
  message?: string;
};

export async function apiStream(
  url: string,
  data: unknown,
  onEvent: (event: ApiStreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    if (response.status === 401 && window.location.pathname !== '/login') {
      window.location.assign('/login');
    }
    let detail = `Request gagal (HTTP ${response.status})`;
    try {
      const payload = await response.json() as { detail?: string };
      detail = payload.detail || detail;
    } catch {
      // Keep the HTTP status message when the server did not return JSON.
    }
    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error('Streaming response tidak tersedia dari server');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const consume = (chunk: string) => {
    buffer += chunk;
    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? '';

    for (const frame of frames) {
      const dataLines = frame
        .split('\n')
        .filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trimStart());

      if (!dataLines.length) continue;

      try {
        onEvent(JSON.parse(dataLines.join('\n')) as ApiStreamEvent);
      } catch {
        // Ignore malformed SSE frames rather than breaking the whole stream.
      }
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    consume(decoder.decode(value, { stream: true }));
  }

  const tail = decoder.decode();
  if (tail) consume(tail);
  if (buffer.trim()) consume('\n\n');
}
