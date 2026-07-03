'use client';

import { useMemo, useState } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { EmptyState } from '@/components/ui/EmptyState';
import { BellIcon, ClockIcon, CheckCircleIcon, XCircleIcon, PawIcon } from '@/components/ui/Icons';
import { parseFecha, sameDay, startOfDay, estadoKey, padTime, fmtDate, escapeHtml } from '@/lib/utils';

export default function NotificacionesPage() {
  const { citas, mascotas } = useDashboard();
  const [readIds, setReadIds] = useState<Set<number>>(new Set());

  const items = useMemo(() => {
    const today = startOfDay(new Date());
    const pendientes = citas.filter((c) => estadoKey(c.estado) === 'pendiente');
    const todays = citas
      .filter((c) => { const d = parseFecha(c.fecha); return d && sameDay(d, today); })
      .sort((a, b) => padTime(a.hora).localeCompare(padTime(b.hora)));
    const upcoming = citas
      .filter((c) => { const d = parseFecha(c.fecha); return d && d.getTime() > today.getTime() && estadoKey(c.estado) !== 'cancelada'; })
      .sort((a, b) => (parseFecha(a.fecha)?.getTime() || 0) - (parseFecha(b.fecha)?.getTime() || 0));

    const result: { id: number; kind: string; title: string; text: string; time: string }[] = [];
    let idx = 0;
    result.push({ id: idx++, kind: 'info', title: 'Asistente IA disponible', text: 'Consulta citas, historiales o crea turnos conversando con el asistente.', time: 'Sistema' });
    if (pendientes.length > 0) {
      result.push({ id: idx++, kind: 'pending', title: `${pendientes.length} ${pendientes.length === 1 ? 'cita pendiente' : 'citas pendientes'} de confirmación`, text: 'Revisa y confirma los turnos pendientes desde la sección Citas.', time: 'Hoy' });
    }
    todays.slice(0, 4).forEach((c) => {
      result.push({ id: idx++, kind: estadoKey(c.estado), title: `Cita de ${c.mascota}`, text: `${c.dueno} a las ${padTime(c.hora)} · ${c.veterinaria}`, time: 'Hoy' });
    });
    upcoming.slice(0, 3).forEach((c) => {
      const d = parseFecha(c.fecha);
      const tomorrow = new Date(today); tomorrow.setDate(tomorrow.getDate() + 1);
      const time = d && sameDay(d, tomorrow) ? 'Mañana' : d ? fmtDate(d) : '';
      result.push({ id: idx++, kind: 'confirmed', title: `Próxima cita: ${c.mascota}`, text: `${c.dueno} · ${time} a las ${padTime(c.hora)}`, time });
    });
    if (mascotas.length > 0) {
      result.push({ id: idx++, kind: 'info', title: `${mascotas.length} pacientes en base`, text: 'Revisa historiales y gestiona citas desde Pacientes.', time: 'Sistema' });
    }
    return result;
  }, [citas, mascotas]);

  const icMap: Record<string, React.ReactNode> = {
    pending: <ClockIcon />,
    confirmed: <CheckCircleIcon />,
    cancelled: <XCircleIcon />,
    info: <PawIcon size={20} />,
    pendiente: <ClockIcon />,
    confirmada: <CheckCircleIcon />,
    cancelada: <XCircleIcon />,
    atendida: <CheckCircleIcon />,
  };

  const unreadCount = items.filter((n) => !readIds.has(n.id)).length;

  return (
    <div className="view active" style={{ display: 'flex' }}>
      <div className="panel">
        <div className="panel-head">
          <div>
            <h2 className="panel-title">Notificaciones</h2>
            <p className="panel-sub">Recordatorios y avisos del sistema</p>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => setReadIds(new Set(items.map((n) => n.id)))}>
            Marcar todo leído
          </button>
        </div>

        {items.length === 0 ? (
          <EmptyState icon={<BellIcon />} title="Todo al día" subtitle="No hay notificaciones pendientes." />
        ) : (
          <div className="notif-list">
            {items.map((n) => (
              <div key={n.id} className={`notif-item ${readIds.has(n.id) ? '' : 'unread'}`}>
                <span className={`notif-ic ${n.kind}`}>{icMap[n.kind] || <PawIcon size={20} />}</span>
                <div className="notif-body">
                  <div className="notif-title">{escapeHtml(n.title)}</div>
                  <div className="notif-text">{escapeHtml(n.text)}</div>
                  <div className="notif-time">{escapeHtml(n.time)}</div>
                </div>
                <span className="notif-dot" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
