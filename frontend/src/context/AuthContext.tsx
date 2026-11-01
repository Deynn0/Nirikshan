import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';
import type { UserRole, UserSession } from '../api/types';

interface AuthContextType {
  session: UserSession | null;
  role: 'applicant' | 'officer' | null;
  isAuthenticated: boolean;
  login: (username: string, role: 'applicant' | 'officer', institutionId?: string) => Promise<void>;
  logout: () => void;
  switchRole: (newRole: 'applicant' | 'officer') => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<UserSession | null>(() => api.getSession());

  useEffect(() => {
    // If no session exists initially, initialize demo officer session so app is immediately usable if desired
    if (!session) {
      const defaultSession: UserSession = {
        token: 'offline-jwt-demo-token-12345',
        username: 'AICTE-Scrutiny-Officer-01',
        role: 'officer',
      };
      api.setSession(defaultSession);
      setSession(defaultSession);
    }
  }, []);

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
        token: `mock-offline-token-${Date.now()}`,
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
