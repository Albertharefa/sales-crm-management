import axios from 'axios';

// Mengambil URL Backend dari environment (saat live di Vercel/Netlify)
// Jika tidak ada (saat coding lokal), akan menggunakan path '/api/v1'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Menyelipkan Token Rahasia (JWT) pada setiap permintaan
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('crm_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Mencegah aplikasi blank (layar putih) jika token kadaluarsa
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      if (status === 401) { // 401 berarti belum login atau sesi habis
        localStorage.removeItem('crm_access_token');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login?expired=true';
        }
      }
    }
    return Promise.reject(error);
  }
);
