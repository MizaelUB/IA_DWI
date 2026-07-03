'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useDashboard } from '@/contexts/DashboardContext';
import { PawIcon, HomeIcon, CalendarIcon, ClipboardIcon, UsersIcon, BellIcon, SparklesIcon, MenuIcon, LogoutIcon } from '@/components/ui/Icons';
import { Avatar } from '@/components/ui/Avatar';

const NAV_GENERAL = [
  { href: '/resumen', label: 'Resumen', icon: <HomeIcon /> },
  { href: '/calendario', label: 'Calendario', icon: <CalendarIcon /> },
  { href: '/citas', label: 'Citas', icon: <ClipboardIcon /> },
  { href: '/pacientes', label: 'Pacientes', icon: <PawIcon size={22} /> },
  { href: '/clientes', label: 'Clientes', icon: <UsersIcon /> },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { citas } = useDashboard();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const pendientes = citas.filter((c) => {
    const e = c.estado?.toLowerCase() || '';
    return e.includes('pend');
  }).length;

  const name = user?.username || user?.veterinary_name || 'Administrador';

  return (
    <>
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'open' : ''}`} aria-label="Navegación principal">
        <div className="sidebar-head">
          <Link className="brand" href="/resumen" aria-label="Swingtails inicio">
            <span className="brand-mark"><PawIcon size={22} /></span>
            <span className="brand-name">Swingtails</span>
          </Link>
          <button className="icon-btn sidebar-toggle" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? 'Expandir menú' : 'Contraer menú'}>
            <MenuIcon />
          </button>
        </div>

        <nav className="nav">
          <p className="nav-label">General</p>
          <ul className="nav-list">
            {NAV_GENERAL.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`nav-item ${pathname === item.href ? 'active' : ''}`}
                  onClick={() => setMobileOpen(false)}
                >
                  <span className="ic">{item.icon}</span>
                  <span className="nav-text">{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>

          <p className="nav-label">Herramientas</p>
          <ul className="nav-list">
            <li>
              <Link
                href="/notificaciones"
                className={`nav-item ${pathname === '/notificaciones' ? 'active' : ''}`}
                onClick={() => setMobileOpen(false)}
              >
                <span className="ic"><BellIcon /></span>
                <span className="nav-text">Notificaciones</span>
                {pendientes > 0 && <span className="nav-badge">{pendientes}</span>}
              </Link>
            </li>
            <li>
              <Link
                href="/asistente"
                className={`nav-item nav-item-ai ${pathname === '/asistente' ? 'active' : ''}`}
                onClick={() => setMobileOpen(false)}
              >
                <span className="nav-ai-glyph"><SparklesIcon /></span>
                <span className="nav-text">Asistente IA</span>
                <span className="nav-ai-pill">Nuevo</span>
              </Link>
            </li>
          </ul>
        </nav>

        <div className="sidebar-foot">
          <div className="user-mini">
            <Avatar name={name} />
            <span className="user-mini-text">
              <span className="user-mini-name">{name}</span>
              <span className="user-mini-role">{user?.veterinary_name || 'Todas las clínicas'}</span>
            </span>
            <button className="icon-btn logout-btn" onClick={logout} aria-label="Cerrar sesión" title="Cerrar sesión">
              <LogoutIcon />
            </button>
          </div>
        </div>
      </aside>

      {mobileOpen && <div className="sidebar-scrim" onClick={() => setMobileOpen(false)} />}

      {/* Mobile menu button - rendered via Topbar */}
    </>
  );
}
