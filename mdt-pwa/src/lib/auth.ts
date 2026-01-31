/**
 * Unified SSO Authentication Client for MDT PWA
 * 
 * Provides seamless authentication across all FusonEMS applications.
 * Tokens issued here work with CAD backend, main app, and other PWAs.
 */

import axios, { AxiosInstance } from 'axios';

const FASTAPI_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8000';
const CAD_BACKEND_URL = import.meta.env.VITE_CAD_BACKEND_URL || 'http://localhost:3000';

interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  org_id: number;
}

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
}

/**
 * SSO Authentication Manager
 */
class SSOAuth {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private user: User | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;

  constructor() {
    this.loadFromStorage();
  }

  /**
   * Load authentication state from localStorage
   */
  private loadFromStorage(): void {
    try {
      const accessToken = localStorage.getItem('sso_access_token');
      const refreshToken = localStorage.getItem('sso_refresh_token');
      const userData = localStorage.getItem('sso_user');

      if (accessToken && refreshToken && userData) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        this.user = JSON.parse(userData);
        this.scheduleTokenRefresh();
      }
    } catch (error) {
      console.error('Error loading auth state from localStorage:', error);
      // Clear storage on error to prevent corrupted state
      try {
        this.clearStorage();
      } catch (clearError) {
        console.error('Error clearing storage:', clearError);
      }
    }
  }

  /**
   * Save authentication state to localStorage
   */
  private saveToStorage(): void {
    if (this.accessToken && this.refreshToken && this.user) {
      try {
        localStorage.setItem('sso_access_token', this.accessToken);
        localStorage.setItem('sso_refresh_token', this.refreshToken);
        localStorage.setItem('sso_user', JSON.stringify(this.user));
      } catch (error) {
        console.error('Error saving auth state to localStorage:', error);
      }
    }
  }

  /**
   * Clear authentication state from localStorage
   */
  private clearStorage(): void {
    try {
      localStorage.removeItem('sso_access_token');
      localStorage.removeItem('sso_refresh_token');
      localStorage.removeItem('sso_user');
      localStorage.removeItem('auth_token'); // Legacy token
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleTokenRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    // Refresh token 5 minutes before expiry (55 minutes for 1-hour tokens)
    const refreshInterval = 55 * 60 * 1000;

    this.refreshTimer = setTimeout(async () => {
      try {
        await this.refresh();
      } catch (error) {
        console.error('Auto-refresh failed:', error);
        this.logout();
      }
    }, refreshInterval);
  }

  /**
   * Login with email and password
   */
  async login(credentials: LoginCredentials): Promise<User> {
    try {
      const response = await axios.post(`${FASTAPI_URL}/api/sso/login`, {
        email: credentials.email,
        password: credentials.password,
        remember_me: credentials.remember_me || false,
        app: 'mdt',
      });

      const { access_token, refresh_token, user } = response.data;

      this.accessToken = access_token;
      this.refreshToken = refresh_token;
      this.user = user;

      this.saveToStorage();
      this.scheduleTokenRefresh();

      return user;
    } catch (error: any) {
      console.error('Login failed:', error);
      throw new Error(
        error.response?.data?.detail || 'Login failed. Please check your credentials.'
      );
    }
  }

  /**
   * Refresh access token
   */
  async refresh(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await axios.post(`${FASTAPI_URL}/api/sso/refresh`, {
        refresh_token: this.refreshToken,
      });

      const { access_token, user } = response.data;

      this.accessToken = access_token;
      this.user = user;

      this.saveToStorage();
      this.scheduleTokenRefresh();
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.logout();
      throw error;
    }
  }

  /**
   * Logout from current session
   */
  async logout(): Promise<void> {
    try {
      if (this.accessToken) {
        await axios.post(
          `${FASTAPI_URL}/api/sso/logout`,
          {},
          {
            headers: {
              Authorization: `Bearer ${this.accessToken}`,
            },
          }
        );
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.accessToken = null;
      this.refreshToken = null;
      this.user = null;

      if (this.refreshTimer) {
        clearTimeout(this.refreshTimer);
      }

      this.clearStorage();
    }
  }

  /**
   * Logout from all devices
   */
  async logoutAll(): Promise<void> {
    try {
      if (this.accessToken) {
        await axios.post(
          `${FASTAPI_URL}/api/sso/logout-all`,
          {},
          {
            headers: {
              Authorization: `Bearer ${this.accessToken}`,
            },
          }
        );
      }
    } catch (error) {
      console.error('Logout all error:', error);
    } finally {
      await this.logout();
    }
  }

  /**
   * Get current authentication state
   */
  getState(): AuthState {
    return {
      user: this.user,
      tokens: this.accessToken && this.refreshToken ? {
        access_token: this.accessToken,
        refresh_token: this.refreshToken,
        token_type: 'bearer',
        expires_in: 3600,
      } : null,
      isAuthenticated: !!this.accessToken && !!this.user,
    };
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Get current user
   */
  getUser(): User | null {
    return this.user;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.accessToken && !!this.user;
  }
}

// Create singleton instance
export const ssoAuth = new SSOAuth();

/**
 * Create authenticated axios instance for FastAPI
 */
export const createFastAPIClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: FASTAPI_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  client.interceptors.request.use((config) => {
    const token = ssoAuth.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          await ssoAuth.refresh();
          const token = ssoAuth.getAccessToken();
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return client(originalRequest);
        } catch (refreshError) {
          ssoAuth.logout();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
};

/**
 * Create authenticated axios instance for CAD Backend
 */
export const createCADClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: CAD_BACKEND_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  client.interceptors.request.use((config) => {
    const token = ssoAuth.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          await ssoAuth.refresh();
          const token = ssoAuth.getAccessToken();
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return client(originalRequest);
        } catch (refreshError) {
          ssoAuth.logout();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
};

export default ssoAuth;
