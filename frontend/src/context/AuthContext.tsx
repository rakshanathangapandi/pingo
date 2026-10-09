import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { getCurrentUser, login, refreshToken } from '@/api/auth';
import { User } from '@/types';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginUser: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const ACCESS_KEY = 'pingo_access_token';
const REFRESH_KEY = 'pingo_refresh_token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const persistTokens = useCallback((access: string, refresh: string) => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  }, []);

  const clearTokens = useCallback(() => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, [clearTokens]);

  const refreshAccessToken = useCallback(async () => {
    const refresh = localStorage.getItem(REFRESH_KEY);
    if (!refresh) {
      logout();
      return;
    }

    try {
      const tokens = await refreshToken(refresh);
      persistTokens(tokens.access_token, tokens.refresh_token);
    } catch {
      logout();
    }
  }, [logout, persistTokens]);

  const loginUser = useCallback(async (email: string, password: string) => {
    const tokens = await login(email, password);
    persistTokens(tokens.access_token, tokens.refresh_token);
    const me = await getCurrentUser();
    setUser(me);
  }, [persistTokens]);

  useEffect(() => {
    const initialize = async () => {
      const access = localStorage.getItem(ACCESS_KEY);
      if (!access) {
        setIsLoading(false);
        return;
      }

      try {
        const me = await getCurrentUser();
        setUser(me);
      } catch {
        await refreshAccessToken();
        try {
          const me = await getCurrentUser();
          setUser(me);
        } catch {
          logout();
        }
      } finally {
        setIsLoading(false);
      }
    };

    void initialize();
  }, [logout, refreshAccessToken]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: !!user, isLoading, loginUser, logout, refreshAccessToken }),
    [loginUser, logout, refreshAccessToken, isLoading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
