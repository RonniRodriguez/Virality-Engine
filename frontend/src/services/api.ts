import axios from 'axios';
import { useAuthStore } from './authStore';

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8080/api/v1', // API Gateway URL
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle 401 (token expiration)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If 401 and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh token
        const refreshToken = useAuthStore.getState().refreshToken;
        if (!refreshToken) {
          throw new Error('No refresh token');
        }
        
        // Call refresh endpoint
        // Note: Create a separate axios instance for refresh to avoid loop
        const refreshResponse = await axios.post('http://localhost:8080/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        });
        
        const { access_token, refresh_token } = refreshResponse.data;
        
        // Update store
        useAuthStore.getState().setTokens(access_token, refresh_token);
        
        // Retry original request
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
        
      } catch (refreshError) {
        // Refresh failed - logout
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;

