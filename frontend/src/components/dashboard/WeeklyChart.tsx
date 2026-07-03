'use client';

import { useMemo } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { parseFecha } from '@/lib/utils';

const W = 700;
const H = 220;
const PAD_X = 8;
const TOP = 26;
const BOTTOM = 28;
const LABELS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

export function WeeklyChart() {
  const { citas } = useDashboard();

  const counts = useMemo(() => {
    const c = [0, 0, 0, 0, 0, 0, 0];
    citas.forEach((appt) => {
      const d = parseFecha(appt.fecha);
      if (d) {
        const day = d.getDay();
        c[day === 0 ? 6 : day - 1]++;
      }
    });
    return c;
  }, [citas]);

  const max = Math.max(1, ...counts);
  const plotH = H - TOP - BOTTOM;
  const baseline = TOP + plotH;
  const slot = (W - PAD_X * 2) / 7;
  const bw = 46;

  return (
    <svg className="chart-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Citas por día de la semana">
      <defs>
        <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#D9663C" />
          <stop offset="1" stopColor="#B5512F" />
        </linearGradient>
      </defs>
      {[0, 0.33, 0.66].map((f) => (
        <line key={f} className="chart-grid" x1={PAD_X} y1={TOP + plotH * f} x2={W - PAD_X} y2={TOP + plotH * f} />
      ))}
      {counts.map((c, i) => {
        const x = PAD_X + i * slot + (slot - bw) / 2;
        const h = c > 0 ? Math.max(6, (c / max) * plotH) : 0;
        const y = baseline - h;
        return (
          <g key={i}>
            {c > 0 ? (
              <>
                <rect className="chart-bar" x={x} y={y} width={bw} height={h} rx={8}>
                  <title>{LABELS[i]}: {c} citas</title>
                </rect>
                <text className="chart-val show" x={x + bw / 2} y={y - 8} textAnchor="middle">{c}</text>
              </>
            ) : (
              <rect className="chart-bar-zero" x={x} y={baseline - 3} width={bw} height={4} rx={2}>
                <title>{LABELS[i]}: 0 citas</title>
              </rect>
            )}
            <text className="chart-axis" x={x + bw / 2} y={H - 8} textAnchor="middle">{LABELS[i]}</text>
          </g>
        );
      })}
      {counts.reduce((a, b) => a + b, 0) === 0 && (
        <text className="chart-axis" x={W / 2} y={H / 2} textAnchor="middle">
          Sin citas suficientes para graficar
        </text>
      )}
    </svg>
  );
}
