'use client';

import { useMemo } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { StatCard } from './StatCard';
import { CalendarIcon, CheckCircleIcon, ClockIcon, PawIcon } from '@/components/ui/Icons';
import { parseFecha, sameDay, startOfDay, estadoKey } from '@/lib/utils';

export function StatsGrid() {
  const { citas, mascotas } = useDashboard();

  const stats = useMemo(() => {
    const today = startOfDay(new Date());
    const todays = citas.filter((c) => {
      const d = parseFecha(c.fecha);
      return d && sameDay(d, today) && estadoKey(c.estado) !== 'cancelada';
    });
    const atendidos = citas.filter((c) => {
      const d = parseFecha(c.fecha);
      return d && sameDay(d, today) && estadoKey(c.estado) === 'atendida';
    });
    const pendientes = citas.filter((c) => estadoKey(c.estado) === 'pendiente');
    return { todays: todays.length, atendidos: atendidos.length, pendientes: pendientes.length, mascotas: mascotas.length };
  }, [citas, mascotas]);

  return (
    <div className="stats-grid">
      <StatCard icon={<CalendarIcon />} sub="hoy" value={stats.todays} label="Citas de hoy" accent="var(--primary)" />
      <StatCard icon={<CheckCircleIcon />} sub="atendidas" value={stats.atendidos} label="Pacientes atendidos" accent="#5E9B86" />
      <StatCard icon={<ClockIcon />} sub="por confirmar" value={stats.pendientes} label="Citas pendientes" accent="#E89A2F" />
      <StatCard icon={<PawIcon />} sub="registrados" value={stats.mascotas} label="Pacientes en base" accent="#B5512F" />
    </div>
  );
}
