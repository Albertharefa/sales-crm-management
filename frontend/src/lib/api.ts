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
