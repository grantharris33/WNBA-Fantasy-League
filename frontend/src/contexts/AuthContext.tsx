import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { api } from '../lib/api';
import type { UserOut, TokenResponse } from '../types';

interface AuthContextType {
  isAuthenticated: boolean;
  user: UserOut | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserOut | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Initialize auth state from localStorage
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    setIsLoading(true);
    const storedToken = localStorage.getItem('auth_token');

    if (storedToken) {
      setToken(storedToken);
      try {
        // Fetch current user with the stored token
        const userData = await api.auth.getMe();
        setUser(userData as UserOut);
        setError(null);
      } catch (err) {
        // Token is invalid or expired
        console.error('Auth initialization error:', err);
        logout();
      }
    }

    setIsLoading(false);
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Get token from login API
      const tokenData = await api.auth.login(email, password) as TokenResponse;

      // Store token in localStorage and state
      localStorage.setItem('auth_token', tokenData.access_token);
      setToken(tokenData.access_token);

      // Fetch current user data
      const userData = await api.auth.getMe();
      setUser(userData as UserOut);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      setToken(null);
      setUser(null);
      localStorage.removeItem('auth_token');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
    setError(null);
  };

  const authValue: AuthContextType = {
    isAuthenticated: !!user,
    user,
    token,
    isLoading,
    error,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={authValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;