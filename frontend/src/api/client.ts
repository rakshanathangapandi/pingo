import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { toast } from 'react-hot-toast';
import { ApiError } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('pingo_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const detail = error.response?.data?.detail ?? error.message ?? 'Request failed';
    if (error.response?.status !== 401) {
      toast.error(detail);
    }
    return Promise.reject(error);
  },
);

export const request = <T>(config: AxiosRequestConfig): Promise<T> =>
  api.request<T>(config).then((response) => response.data);

export default api;
