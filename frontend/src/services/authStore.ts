import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  roles: string[];
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  
  // Actions
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  login: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      
      setTokens: (accessToken, refreshToken) => 
        set({ accessToken, refreshToken }),
        
      setUser: (user) => 
        set({ user, isAuthenticated: true }),
        
      login: (user, accessToken, refreshToken) => 
        set({ user, accessToken, refreshToken, isAuthenticated: true }),
        
      logout: () => 
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),
    }),
    {
      name: 'idea-inc-auth', // Key in localStorage
      partialize: (state) => ({ 
        accessToken: state.accessToken, 
        refreshToken: state.refreshToken,
        user: state.user, // Persist user info too for immediate UI
      }), 
    }
  )
);

