'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDashboard } from '@/contexts/DashboardContext';
import { DateStrip } from '@/components/calendario/DateStrip';
import { AgendaList } from '@/components/calendario/AgendaList';
import { ChevronLeftIcon, ChevronRightIcon } from '@/components/ui/Icons';
import { startOfDay, WD_FULL, fmtDate } from '@/lib/utils';

export default function CalendarioPage() {
  const { citas } = useDashboard();
  const router = useRouter();
  const [selectedDate, setSelectedDate] = useState(() => startOfDay(new Date()));
  const [calStart, setCalStart] = useState(() => startOfDay(new Date()));

  const handleAskAI = useCallback(
    (prompt: string) => {
      localStorage.setItem('pending_ai_prompt', prompt);
      router.push('/asistente');
    },
    [router],
  );

  return (
    <div className="view active" style={{ display: 'flex' }}>
      <div className="panel">
        <div className="panel-head">
          <div>
            <h2 className="panel-title">Agenda</h2>
            <p className="panel-sub">{WD_FULL[selectedDate.getDay()]} · {fmtDate(selectedDate)}</p>
          </div>
          <div className="date-nav">
            <button className="icon-btn" onClick={() => { const d = new Date(calStart); d.setDate(d.getDate() - 7); setCalStart(d); }} aria-label="Semana anterior">
              <ChevronLeftIcon />
            </button>
            <button className="icon-btn" onClick={() => { const d = new Date(calStart); d.setDate(d.getDate() + 7); setCalStart(d); }} aria-label="Semana siguiente">
              <ChevronRightIcon />
            </button>
          </div>
        </div>
        <DateStrip citas={citas} calStart={calStart} selectedDate={selectedDate} onSelect={setSelectedDate} />
        <AgendaList citas={citas} selectedDate={selectedDate} onAskAI={handleAskAI} />
      </div>
    </div>
  );
}
