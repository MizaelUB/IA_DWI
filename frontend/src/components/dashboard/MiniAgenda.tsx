'use client';

import { useMemo } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { parseFecha, sameDay, startOfDay, estadoKey, padTime, escapeHtml } from '@/lib/utils';

export function MiniAgenda() {
  const { citas } = useDashboard();

  const items = useMemo(() => {
    const today = startOfDay(new Date());
    return citas
      .filter((c) => {
        const d = parseFecha(c.fecha);
        return d && sameDay(d, today) && estadoKey(c.estado) !== 'cancelada';
      })
      .sort((a, b) => padTime(a.hora).localeCompare(padTime(b.hora)))
      .slice(0, 6);
  }, [citas]);

  if (items.length === 0) {
    return (
      <div className="mini-agenda">
        <EmptyState icon={<span />} title="Sin citas para hoy" subtitle="Crea una cita desde el asistente IA." />
      </div>
    );
  }

  return (
    <div className="mini-agenda">
      {items.map((c) => (
        <div className="mini-agenda-item" key={c.id}>
          <span className="mini-time">{escapeHtml(padTime(c.hora))}</span>
          <span className="mini-info">
            <span className="mini-pet">{escapeHtml(c.mascota)}</span>
            <span className="mini-owner">{escapeHtml(c.dueno)}</span>
          </span>
          <StatusBadge estado={c.estado} />
        </div>
      ))}
    </div>
  );
}
