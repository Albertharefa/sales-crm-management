import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Interceptor untuk Token
apiClient.interceptors.request.use(
  (config: any) => {
    const token = localStorage.getItem('crm_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: any) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response: any) => response,
  (error: any) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('crm_access_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?expired=true';
      }
    }
    return Promise.reject(error);
  }
);

// Helper Methods yang dipanggil oleh halaman-halaman frontend
export const apiGet = async (url: string, config?: any) => {
  const response = await apiClient.get(url, config);
  return response.data;
};

export const apiPost = async (url: string, data?: any, config?: any) => {
  const response = await apiClient.post(url, data, config);
  return response.data;
};

export const apiPut = async (url: string, data?: any, config?: any) => {
  const response = await apiClient.put(url, data, config);
  return response.data;
};

export const apiPatch = async (url: string, data?: any, config?: any) => {
  const response = await apiClient.patch(url, data, config);
  return response.data;
};

export const apiDelete = async (url: string, config?: any) => {
  const response = await apiClient.delete(url, config);
  return response.data;
};

export const apiUpload = async (url: string, formData: FormData, config?: any) => {
  const response = await apiClient.post(url, formData, {
    ...config,
    headers: {
      ...config?.headers,
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export interface ApiError extends Error {
  status?: number;
  response?: any;
}
