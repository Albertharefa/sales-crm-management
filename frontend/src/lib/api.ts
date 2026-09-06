import axios from 'axios';

// Otomatis mendeteksi URL backend Railway atau fallback ke localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://sales-crm-management-production.up.railway.app';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('crm_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});
