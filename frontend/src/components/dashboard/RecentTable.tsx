'use client';

import { useMemo } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PetAvatar } from '@/components/ui/Avatar';
import { parseFecha, padTime, escapeHtml } from '@/lib/utils';

export function RecentTable() {
  const { citas } = useDashboard();

  const rows = useMemo(() => {
    return citas
      .slice()
      .sort((a, b) => {
        const da = parseFecha(a.fecha);
        const db = parseFecha(b.fecha);
        return (db ? db.getTime() : 0) - (da ? da.getTime() : 0);
      })
      .slice(0, 6);
  }, [citas]);

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Hora</th>
            <th>Mascota</th>
            <th>Dueño</th>
            <th>Clínica</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '28px' }}>
                Aún no hay citas registradas.
              </td>
            </tr>
          ) : (
            rows.map((c) => (
              <tr key={c.id}>
                <td className="cell-muted">{escapeHtml(c.fecha)}</td>
                <td className="cell-strong">{escapeHtml(padTime(c.hora))}</td>
                <td>
                  <div className="pet-cell">
                    <PetAvatar name={c.mascota} />
                    <span className="cell-strong">{escapeHtml(c.mascota)}</span>
                  </div>
                </td>
                <td>{escapeHtml(c.dueno)}</td>
                <td className="cell-muted">{escapeHtml(c.veterinaria)}</td>
                <td><StatusBadge estado={c.estado} /></td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
