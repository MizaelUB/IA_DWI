'use client';

import { WD, parseFecha, sameDay, startOfDay } from '@/lib/utils';
import type { Cita } from '@/lib/types';

interface DateStripProps {
  citas: Cita[];
  calStart: Date;
  selectedDate: Date;
  onSelect: (d: Date) => void;
}

export function DateStrip({ citas, calStart, selectedDate, onSelect }: DateStripProps) {
  const today = startOfDay(new Date());
  const pills: React.ReactNode[] = [];

  for (let i = 0; i < 14; i++) {
    const d = new Date(calStart);
    d.setDate(d.getDate() + i);
    const count = citas.filter((c) => {
      const cd = parseFecha(c.fecha);
      return cd && sameDay(cd, d);
    }).length;
    const isToday = sameDay(d, today);
    const isActive = sameDay(d, selectedDate);

    pills.push(
      <button
        key={i}
        className={`date-pill ${isActive ? 'active' : ''} ${isToday ? 'today' : ''}`}
        onClick={() => onSelect(startOfDay(new Date(d)))}
        role="tab"
        aria-selected={isActive}
      >
        <span className="date-pill-dow">{WD[d.getDay()]}</span>
        <span className="date-pill-day">{d.getDate()}</span>
        <span className="date-pill-count">{count} {count === 1 ? 'cita' : 'citas'}</span>
      </button>,
    );
  }

  return (
    <div className="date-strip" role="tablist" aria-label="Días">
      {pills}
    </div>
  );
}
