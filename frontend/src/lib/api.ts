import axios, { isAxiosError } from 'axios';
import Cookies from 'js-cookie';

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!isAxiosError<{ detail?: unknown }>(error)) {
    return fallback;
  }

  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail.flatMap((item) => {
      if (typeof item === 'string') {
        return [item];
      }
      if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') {
        return [item.msg];
      }
      return [];
    });
    if (messages.length > 0) {
      return messages.join(' ');
    }
  }

  return fallback;
}

const api = axios.create({
  baseURL: (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/+$/, ''),
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = Cookies.get('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
