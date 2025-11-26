export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  roles: string[];
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  display_name?: string;
}

