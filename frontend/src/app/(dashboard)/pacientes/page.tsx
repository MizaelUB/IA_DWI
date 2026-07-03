'use client';

import { useState, useMemo } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { PatientAvatar } from '@/components/ui/Avatar';
import { EmptyState } from '@/components/ui/EmptyState';
import { PawIcon, UserIcon, CalendarIcon } from '@/components/ui/Icons';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { escapeHtml } from '@/lib/utils';

export default function PacientesPage() {
  const { mascotas } = useDashboard();
  const [expandedPetId, setExpandedPetId] = useState<number | null>(null);

  const list = useMemo(() => mascotas, [mascotas]);

  return (
    <div className="view active" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="view-head">
        <div>
          <h2 className="panel-title">Pacientes</h2>
          <p className="panel-sub">Mascotas registradas y sus responsables</p>
        </div>
      </div>

      {list.length === 0 ? (
        <EmptyState
          icon={<PawIcon />}
          title="Sin pacientes registrados"
          subtitle="Los pacientes aparecerán aquí cuando se registren."
        />
      ) : (
        <div className="cards-grid">
          {list.map((m) => (
            <article className="patient-card" key={m.id} style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div className="patient-head">
                <PatientAvatar name={m.nombre} />
                <div>
                  <div className="patient-name">{escapeHtml(m.nombre)}</div>
                  <div className="patient-species">{escapeHtml(m.especie)}{m.raza ? ` · ${escapeHtml(m.raza)}` : ''}</div>
                </div>
              </div>
              <div className="patient-rows" style={{ flexGrow: 1 }}>
                <div className="patient-row"><UserIcon /><span>Dueño: <b>{escapeHtml(m.dueno)}</b></span></div>
                <div className="patient-row"><PawIcon size={16} /><span>ID <b>#{escapeHtml(String(m.id))}</b></span></div>
              </div>
              
              {expandedPetId === m.id && (
                <div className="patient-appointments" style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <h4 style={{ fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
                    <span style={{ width: 16, height: 16, display: 'inline-block' }}><CalendarIcon /></span> Citas de la mascota
                  </h4>
                  {m.citas && m.citas.length > 0 ? (
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {m.citas.map((c) => (
                        <li key={c.id} style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: 4, padding: '8px', background: 'var(--bg-light)', borderRadius: 6, border: '1px solid var(--border)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: 600 }}>{c.fecha} - {c.hora.substring(0, 5)}</span>
                            <StatusBadge estado={c.estado} />
                          </div>
                          {c.notas && (
                            <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                              Nota: {c.notas}
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>Sin citas registradas</p>
                  )}
                </div>
              )}

              <div className="patient-foot" style={{ marginTop: 12 }}>
                <button 
                  className="btn btn-ghost btn-sm" 
                  onClick={() => setExpandedPetId(expandedPetId === m.id ? null : m.id)} 
                  style={{ flex: 1 }}
                >
                  {expandedPetId === m.id ? 'Ocultar historial' : 'Ver historial'}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
