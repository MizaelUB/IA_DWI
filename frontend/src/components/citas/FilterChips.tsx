'use client';

const FILTERS = [
  { key: 'todas', label: 'Todas' },
  { key: 'pendiente', label: 'Pendientes' },
  { key: 'confirmada', label: 'Confirmadas' },
  { key: 'cancelada', label: 'Canceladas' },
];

export function FilterChips({ active, onChange }: { active: string; onChange: (f: string) => void }) {
  return (
    <div className="filter-chips" role="group" aria-label="Filtrar por estado">
      {FILTERS.map((f) => (
        <button
          key={f.key}
          className={`chip ${active === f.key ? 'active' : ''}`}
          onClick={() => onChange(f.key)}
        >
          {f.label}
        </button>
      ))}
    </div>
  );
}
