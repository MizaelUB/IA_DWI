'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import type { Session, RegisterRequest } from '@/lib/types';
import { login as apiLogin, register as apiRegister } from '@/lib/api';

interface AuthContextType {
  user: Session | null;
  isLoading: boolean;
  login: (username: string, password: string, captchaId?: string, captchaAnswer?: string) => Promise<{ success: boolean; error?: string; requiresCaptcha?: boolean }>;
  register: (data: RegisterRequest) => Promise<{ success: boolean; error?: string; message?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    fetch('/api/auth/me')
      .then(res => {
        if (res.ok) return res.json();
        throw new Error('Not authenticated');
      })
      .then(data => {
        setUser({
          username: data.username || 'Usuario',
          veterinary_id: data.veterinary_id || null,
          veterinary_name: data.veterinary_name || 'Clínica Veterinaria Prueba IA',
          user_id: data.user_id || null,
        });
        setIsLoading(false);
      })
      .catch(() => {
        setUser(null);
        setIsLoading(false);
      });
  }, []);

  const login = useCallback(async (username: string, password: string, captchaId?: string, captchaAnswer?: string) => {
    const data = await apiLogin(username, password, captchaId, captchaAnswer);
    if (data.status === 'success') {
      const session: Session = {
        username: data.username,
        veterinary_id: data.veterinary_id,
        veterinary_name: data.veterinary_name,
        user_id: data.user_id,
      };
      setUser(session);
      return { success: true };
    }
    
    if (data.detail && typeof data.detail === 'object' && data.detail.error === 'CAPTCHA_REQUIRED') {
      return { success: false, requiresCaptcha: true, error: data.detail.message };
    }
    
    if (data.detail && typeof data.detail === 'object' && data.detail.error === 'RATE_LIMITED') {
      return { success: false, error: data.detail.message };
    }
    
    return { success: false, error: typeof data.detail === 'string' ? data.detail : 'Usuario o contraseña incorrectos.' };
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    try {
      const result = await apiRegister(data);
      if (result.status === 'success') {
        return { success: true, message: result.message };
      }
      return { success: false, error: typeof result.detail === 'string' ? result.detail : 'Error al registrar.' };
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : 'Error al conectar' };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (_) {}
    try {
      await fetch('/api/chat/history', { method: 'DELETE' });
    } catch (_) {}
    setUser(null);
    router.push('/login');
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
