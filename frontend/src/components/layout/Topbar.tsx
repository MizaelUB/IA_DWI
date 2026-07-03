'use client';

import { useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useDashboard } from '@/contexts/DashboardContext';
import { VIEW_TITLES } from '@/lib/constants';
import { MenuIcon, SearchIcon, BellIcon } from '@/components/ui/Icons';

export function Topbar({ onSearch, onMenuClick }: { onSearch?: (q: string) => void; onMenuClick?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const { veterinarias, selectedVetId, setSelectedVetId, citas } = useDashboard();
  const [searchValue, setSearchValue] = useState('');

  const viewKey = pathname.replace('/', '') || 'resumen';
  const title = VIEW_TITLES[viewKey] || 'Swingtails';

  const pendientes = citas.filter((c) => (c.estado?.toLowerCase() || '').includes('pend')).length;

  const handleSearch = (value: string) => {
    setSearchValue(value);
    onSearch?.(value);
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button className="icon-btn menu-btn" onClick={onMenuClick} aria-label="Abrir menú">
          <MenuIcon />
        </button>
        <h1 className="page-title">{title}</h1>
      </div>
      <div className="topbar-right">
        <div className="search">
          <SearchIcon />
          <input
            type="search"
            placeholder="Buscar citas, pacientes…"
            aria-label="Buscar"
            value={searchValue}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </div>
        <select
          className="clinic-select"
          aria-label="Clínica"
          value={selectedVetId}
          onChange={(e) => setSelectedVetId(e.target.value)}
        >
          <option value="">Todas las clínicas</option>
          {veterinarias.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}{v.city ? ` (${v.city})` : ''}
            </option>
          ))}
        </select>
        <button className="icon-btn bell-btn" onClick={() => router.push('/notificaciones')} aria-label="Notificaciones">
          <BellIcon />
          {pendientes > 0 && <span className="bell-dot" />}
        </button>
      </div>
    </header>
  );
}
