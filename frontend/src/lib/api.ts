import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  response => response,
  error => {
    if (error?.response?.status === 401 && window.location.pathname !== '/login') {
      window.location.assign('/login');
    }
    return Promise.reject(error);
  },
);

export const apiGet = <T>(url: string) => api.get<T>(url).then(r => r.data);
export const apiPost = <T>(url: string, data?: unknown) => api.post<T>(url, data).then(r => r.data);
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
