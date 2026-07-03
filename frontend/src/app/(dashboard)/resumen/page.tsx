'use client';

import Link from 'next/link';
import { StatsGrid } from '@/components/dashboard/StatsGrid';
import { WeeklyChart } from '@/components/dashboard/WeeklyChart';
import { MiniAgenda } from '@/components/dashboard/MiniAgenda';
import { RecentTable } from '@/components/dashboard/RecentTable';

export default function ResumenPage() {
  return (
    <div className="view active" style={{ display: 'flex' }}>
      <StatsGrid />

      <div className="overview-grid">
        <div className="panel chart-panel">
          <div className="panel-head">
            <div>
              <h2 className="panel-title">Citas de la semana</h2>
              <p className="panel-sub">Distribución por día de la semana</p>
            </div>
            <span className="legend"><span className="legend-dot" /> Citas</span>
          </div>
          <div className="chart-wrap"><WeeklyChart /></div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <h2 className="panel-title">Próximas citas</h2>
              <p className="panel-sub">Agenda de hoy</p>
            </div>
            <Link className="btn btn-ghost btn-sm" href="/calendario">Ver calendario</Link>
          </div>
          <MiniAgenda />
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <h2 className="panel-title">Citas recientes</h2>
            <p className="panel-sub">Últimos registros del sistema</p>
          </div>
          <Link className="btn btn-ghost btn-sm" href="/citas">Ver todas</Link>
        </div>
        <RecentTable />
      </div>
    </div>
  );
}
