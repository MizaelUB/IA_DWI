'use client';

import { useMemo } from 'react';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { CalendarIcon, EllipsisIcon } from '@/components/ui/Icons';
import { parseFecha, sameDay, estadoKey, padTime, escapeHtml } from '@/lib/utils';
import type { Cita } from '@/lib/types';

export function AgendaList({ citas, selectedDate, onAskAI }: { citas: Cita[]; selectedDate: Date; onAskAI?: (prompt: string) => void }) {
  const items = useMemo(() => {
    return citas
      .filter((c) => {
        const d = parseFecha(c.fecha);
        return d && sameDay(d, selectedDate);
      })
      .sort((a, b) => padTime(a.hora).localeCompare(padTime(b.hora)));
  }, [citas, selectedDate]);

  if (items.length === 0) {
    return (
      <div className="agenda-list">
        <EmptyState
          icon={<CalendarIcon />}
          title="No hay citas este día"
          subtitle="Selecciona otro día o crea una cita desde el asistente."
        />
      </div>
    );
  }

  return (
    <div className="agenda-list">
      {items.map((c) => {
        const k = estadoKey(c.estado);
        return (
          <div className={`agenda-item is-${k}`} key={c.id}>
            <span className="agenda-time">{escapeHtml(padTime(c.hora))}</span>
            <div className="agenda-body">
              <div className="agenda-pet">{escapeHtml(c.mascota)}</div>
              <div className="agenda-meta">{escapeHtml(c.dueno)} · {escapeHtml(c.veterinaria)}</div>
            </div>
            <div className="agenda-side">
              <StatusBadge estado={c.estado} />
              <button
                className="icon-btn"
                onClick={() => onAskAI?.(`Muéstrame los detalles de la cita de ${c.mascota} el ${c.fecha}`)}
                aria-label="Consultar"
                style={{ width: 32, height: 32 }}
              >
                <EllipsisIcon />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
