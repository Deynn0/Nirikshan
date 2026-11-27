import React, { createContext, useContext, useEffect, useState } from 'react';
import { QueryClientContext } from '@tanstack/react-query';
import { api } from '../api/client';
import type { UserSession } from '../api/types';

interface AuthContextType {
  session: UserSession | null;
  role: 'applicant' | 'officer' | null;
  isAuthenticated: boolean;
  login: (username: string, role: 'applicant' | 'officer', institutionId?: string) => Promise<void>;
  logout: () => void;
  switchRole: (newRole: 'applicant' | 'officer') => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const LEGACY_AUTO_LOGIN_TOKEN = 'offline-jwt-demo-token-12345';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useContext(QueryClientContext);
  const [session, setSession] = useState<UserSession | null>(() => {
    const saved = api.getSession();
    if (saved?.token === LEGACY_AUTO_LOGIN_TOKEN) {
      api.setSession(null);
      return null;
    }
    return saved;
  });

  useEffect(() => {
    const sync = () => setSession(api.getSession());
    window.addEventListener('nirikshan-session-changed', sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener('nirikshan-session-changed', sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  // No auto-login: users must authenticate explicitly via the login page.

  const login = async (username: string, role: 'applicant' | 'officer', institutionId?: string) => {
    try {
      const res = await api.login({
        username,
        role: role as any,
        password: 'offline-password',
        institution_id: institutionId,
      });
      const newSession: UserSession = {
        token: res.access_token,
        username: res.username,
        role,
        institutionId,
      };
      api.setSession(newSession);
      setSession(newSession);
    } catch {
      // Offline fallback: generate mock token if backend auth route is unavailable
      const fallbackSession: UserSession = {
        token: `offline-session-${Date.now()}`,
        username,
        role,
        institutionId,
      };
      api.setSession(fallbackSession);
      setSession(fallbackSession);
    }
  };

  const logout = () => {
    api.setSession(null);
    setSession(null);
    queryClient?.setQueryData(['me'], null);
  };

  const switchRole = (newRole: 'applicant' | 'officer') => {
    if (session) {
      const updated = { ...session, role: newRole };
      api.setSession(updated);
      setSession(updated);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        session,
        role: session?.role || null,
        isAuthenticated: !!session,
        login,
        logout,
        switchRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
