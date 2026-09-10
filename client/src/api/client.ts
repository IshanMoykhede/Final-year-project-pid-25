import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // required to send the HttpOnly cookie for auth
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error.config as (typeof error.config & { _retry?: boolean }) | undefined;

    if (error.response?.status === 401 && request && !request._retry && !request.url?.includes('/auth/refresh')) {
      request._retry = true;
      try {
        await apiClient.post('/auth/refresh');
        return apiClient(request);
      } catch {
        window.dispatchEvent(new Event('unauthorized'));
      }
    }

    return Promise.reject(error);
  }
);
