'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import type { Session } from '@/lib/types';
import { login as apiLogin } from '@/lib/api';

interface AuthContextType {
  user: Session | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const stored = localStorage.getItem('clinic_session');
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem('clinic_session');
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const data = await apiLogin(username, password);
    if (data.status === 'success') {
      const session: Session = {
        username: data.username,
        veterinary_id: data.veterinary_id,
        veterinary_name: data.veterinary_name,
      };
      localStorage.setItem('clinic_session', JSON.stringify(session));
      setUser(session);
      return { success: true };
    }
    return { success: false, error: data.detail || 'Usuario o contraseña incorrectos.' };
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('clinic_session');
    localStorage.removeItem('conversation_id');
    setUser(null);
    router.push('/login');
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
