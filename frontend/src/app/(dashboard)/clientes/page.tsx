'use client';

import { useMemo } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { PatientAvatar } from '@/components/ui/Avatar';
import { EmptyState } from '@/components/ui/EmptyState';
import { UsersIcon, PhoneIcon, MailIcon } from '@/components/ui/Icons';
import { escapeHtml } from '@/lib/utils';

export default function ClientesPage() {
  const { clientes } = useDashboard();
  const list = useMemo(() => clientes, [clientes]);

  return (
    <div className="view active" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="view-head">
        <div>
          <h2 className="panel-title">Clientes</h2>
          <p className="panel-sub">Dueños y datos de contacto</p>
        </div>
      </div>

      {list.length === 0 ? (
        <EmptyState
          icon={<UsersIcon />}
          title="Sin clientes registrados"
          subtitle="Los clientes aparecerán aquí cuando se registren."
        />
      ) : (
        <div className="cards-grid cards-grid-sm">
          {list.map((c) => (
            <article className="client-card" key={c.id}>
              <div className="client-head">
                <PatientAvatar name={c.nombre} />
                <div className="client-name">{escapeHtml(c.nombre)}</div>
              </div>
              <div className="client-rows">
                {c.telefono && (
                  <div className="client-row"><PhoneIcon /><span>{escapeHtml(c.telefono)}</span></div>
                )}
                {c.email && (
                  <div className="client-row"><MailIcon /><span>{escapeHtml(c.email)}</span></div>
                )}
                <div className="client-row"><UsersIcon /><span>ID <b>#{escapeHtml(c.id)}</b></span></div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
