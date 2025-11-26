import { useMutation } from '@tanstack/react-query';
import api from '../services/api';
import { useAuthStore } from '../services/authStore';
import type { LoginCredentials, RegisterCredentials, AuthResponse, User } from '../types/auth';

export const useAuth = () => {
  const { login, logout } = useAuthStore();

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const response = await api.post<AuthResponse>('/auth/login', credentials);
      return response.data;
    },
    onSuccess: async (data) => {
      // After login, we need to fetch the user profile
      // We set tokens first so the next request is authenticated
      useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
      
      // Fetch user profile immediately
      const userResponse = await api.get<User>('/auth/me');
      login(userResponse.data, data.access_token, data.refresh_token);
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: async (credentials: RegisterCredentials) => {
      const response = await api.post<AuthResponse>('/auth/register', credentials);
      return response.data;
    },
    onSuccess: async (data) => {
      useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
      const userResponse = await api.get<User>('/auth/me');
      login(userResponse.data, data.access_token, data.refresh_token);
    },
  });

  // Logout
  const performLogout = () => {
    // Optionally call logout endpoint
    api.post('/auth/logout').catch(() => {}); // Ignore errors
    logout();
  };

  return {
    login: loginMutation,
    register: registerMutation,
    logout: performLogout,
  };
};
