'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { PawIcon } from '@/components/ui/Icons';

export default function LoginPage() {
  const { user, isLoading, login, loginAsGuest } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && user) router.replace('/asistente');
  }, [user, isLoading, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;
    setError('');
    setSubmitting(true);
    const result = await login(username.trim(), password.trim());
    if (result.success) {
      router.push('/asistente');
    } else {
      setError(result.error || 'Error desconocido');
    }
    setSubmitting(false);
  };

  const handleGuestLogin = async () => {
    setError('');
    setSubmitting(true);
    const result = await loginAsGuest();
    if (result.success) {
      router.push('/asistente');
    } else {
      setError(result.error || 'Error al conectar');
    }
    setSubmitting(false);
  };

  if (isLoading || user) return null;

  return (
    <div className="login">
      <aside className="login-aside">
        <div className="login-aside-glow" aria-hidden="true" />
        <svg className="login-aside-paw" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 13.2c-2.4 0-4.3 1.7-4.3 3.8 0 1.1.9 1.8 2 1.8.9 0 1.5-.3 2.3-.3s1.4.3 2.3.3c1.1 0 2-.7 2-1.8 0-2.1-1.9-3.8-4.3-3.8Z"/><ellipse cx="6.7" cy="11" rx="1.6" ry="2"/><ellipse cx="17.3" cy="11" rx="1.6" ry="2"/><ellipse cx="9.7" cy="7.6" rx="1.5" ry="1.9"/><ellipse cx="14.3" cy="7.6" rx="1.5" ry="1.9"/></svg>
        <div className="login-aside-top">
          <span className="login-aside-mark"><PawIcon size={24} /></span>
          <span className="login-aside-name">Swingtails</span>
        </div>
        <div className="login-aside-body">
          <h2 className="login-aside-title">Gestión veterinaria</h2>
          <p className="login-aside-sub">Citas, pacientes y clientes en un solo panel.</p>
        </div>
        <p className="login-aside-foot">Panel para personal administrativo y veterinarios.</p>
      </aside>

      <main className="login-main">
        <div className="login-card">
          <div className="login-head">
            <h1 className="login-title">Iniciar sesión</h1>
            <p className="login-subtitle">Accede al panel de Swingtails</p>
          </div>
          <form className="login-form" onSubmit={handleSubmit} autoComplete="on">
            <div className="field">
              <label htmlFor="login-username">Usuario</label>
              <input
                type="text"
                id="login-username"
                name="username"
                placeholder="admin_ia"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="login-password">Contraseña</label>
              <input
                type="password"
                id="login-password"
                name="password"
                placeholder="••••••••"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <p className="login-error" role="alert">{error}</p>
            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? 'Conectando…' : 'Iniciar sesión'}
            </button>
            <div style={{ textAlign: 'center', margin: '12px 0', fontSize: '0.9rem', color: 'var(--text-muted)' }}>o</div>
            <button type="button" onClick={handleGuestLogin} className="btn btn-ghost btn-block" disabled={submitting}>
              Continuar como invitado
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
