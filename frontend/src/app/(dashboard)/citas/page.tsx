'use client';

import { useState, useMemo } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { FilterChips } from '@/components/citas/FilterChips';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PetAvatar } from '@/components/ui/Avatar';
import { EmptyState } from '@/components/ui/EmptyState';
import { DocumentIcon, EllipsisIcon } from '@/components/ui/Icons';
import { estadoKey, padTime, escapeHtml } from '@/lib/utils';

export default function CitasPage() {
  const { citas } = useDashboard();
  const [filter, setFilter] = useState('todas');
  const [search, setSearch] = useState('');
  const [expandedCitaId, setExpandedCitaId] = useState<number | null>(null);

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return citas
      .filter((c) => {
        if (filter !== 'todas' && estadoKey(c.estado) !== filter) return false;
        if (q) {
          const hay = `${c.mascota} ${c.dueno} ${c.veterinaria} ${c.fecha} ${c.hora} #${c.id}`.toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      })
      .sort((a, b) => padTime(a.hora).localeCompare(padTime(b.hora)));
  }, [citas, filter, search]);

  return (
    <div className="view active" style={{ display: 'flex' }}>
      <div className="panel">
        <div className="panel-head panel-head-stack">
          <div>
            <h2 className="panel-title">Gestión de citas</h2>
            <p className="panel-sub">Filtra y revisa el estado de cada turno</p>
          </div>
          <FilterChips active={filter} onChange={setFilter} />
        </div>
        {rows.length === 0 ? (
          <EmptyState
            icon={<DocumentIcon />}
            title="No hay citas en este filtro"
            subtitle="Cambia el filtro o revisa la agenda."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Mascota</th>
                  <th>Dueño</th>
                  <th>Fecha</th>
                  <th>Hora</th>
                  <th>Clínica</th>
                  <th>Estado</th>
                  <th className="th-end" />
                </tr>
              </thead>
              <tbody>
                {rows.flatMap((c) => {
                  const isExpanded = expandedCitaId === c.id;
                  return [
                    <tr key={c.id}>
                      <td className="cell-id">#{escapeHtml(String(c.id))}</td>
                      <td>
                        <div className="pet-cell">
                          <PetAvatar name={c.mascota} />
                          <span className="cell-strong">{escapeHtml(c.mascota)}</span>
                        </div>
                      </td>
                      <td>{escapeHtml(c.dueno)}</td>
                      <td className="cell-muted">{escapeHtml(c.fecha)}</td>
                      <td className="cell-strong">{escapeHtml(padTime(c.hora))}</td>
                      <td className="cell-muted">{escapeHtml(c.veterinaria)}</td>
                      <td><StatusBadge estado={c.estado} /></td>
                      <td className="td-end">
                        <button
                          className="icon-btn row-action"
                          onClick={() => setExpandedCitaId(isExpanded ? null : c.id)}
                          aria-label={`Consultar cita #${c.id}`}
                          style={{ 
                            width: 32, 
                            height: 32, 
                            transform: isExpanded ? 'rotate(90deg)' : 'none', 
                            transition: 'transform 0.2s',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          <EllipsisIcon />
                        </button>
                      </td>
                    </tr>,
                    isExpanded && (
                      <tr key={`${c.id}-details`} style={{ background: 'var(--bg-light)' }}>
                        <td colSpan={8} style={{ padding: '12px 24px', borderTop: 'none' }}>
                          <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                            <div style={{ fontWeight: 600 }}>
                              Detalles de la Cita #{c.id}
                            </div>
                            <div><b>Mascota:</b> {escapeHtml(c.mascota)}</div>
                            <div><b>Dueño:</b> {escapeHtml(c.dueno)}</div>
                            <div><b>Clínica:</b> {escapeHtml(c.veterinaria)}</div>
                            <div><b>Fecha y Hora:</b> {escapeHtml(c.fecha)} a las {escapeHtml(padTime(c.hora))}</div>
                            <div><b>Notas:</b> {c.notas ? escapeHtml(c.notas) : <span style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>Sin notas registradas.</span>}</div>
                          </div>
                        </td>
                      </tr>
                    )
                  ];
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
