'use client';

import { useEffect, useState } from 'react';

import { useAuth } from '@/contexts/AuthContext';
import { PatientAvatar } from '@/components/ui/Avatar';
import { EmptyState } from '@/components/ui/EmptyState';
import { UsersIcon, PhoneIcon, MailIcon } from '@/components/ui/Icons';
import { escapeHtml } from '@/lib/utils';
import { fetchClientes, PaginatedResponse } from '@/lib/api';
import type { Cliente } from '@/lib/types';

export default function ClientesPage() {
  const { user } = useAuth();
  const [data, setData] = useState<PaginatedResponse<Cliente>>({ 
    data: [], 
    pagination: { total: 0, page: 1, limit: 10, total_pages: 1 } 
  });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.veterinary_id) {
      setLoading(true);
      fetchClientes(String(user.veterinary_id), page).then((res) => {
        setData(res);
        setLoading(false);
      });
    }
  }, [user, page]);

  return (
    <div className="view active" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="view-head">
        <div>
          <h2 className="panel-title">Clientes</h2>
          <p className="panel-sub">Dueños y datos de contacto</p>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>Cargando clientes...</div>
      ) : data.data.length === 0 ? (
        <EmptyState
          icon={<UsersIcon />}
          title="Sin clientes registrados"
          subtitle="Los clientes aparecerán aquí cuando se registren."
        />
      ) : (
        <>
          <div className="cards-grid cards-grid-sm">
            {data.data.map((c) => (
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
          
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
            <button 
              className="btn btn-secondary" 
              disabled={data.pagination.page <= 1}
              onClick={() => setPage(p => p - 1)}
            >
              Anterior
            </button>
            <span>Página {data.pagination.page} de {data.pagination.total_pages}</span>
            <button 
              className="btn btn-secondary" 
              disabled={data.pagination.page >= data.pagination.total_pages}
              onClick={() => setPage(p => p + 1)}
            >
              Siguiente
            </button>
          </div>
        </>
      )}
    </div>
  );
}
