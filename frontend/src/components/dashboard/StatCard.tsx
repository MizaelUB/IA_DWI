import { ReactNode } from 'react';

export function StatCard({
  icon,
  sub,
  value,
  label,
  accent,
}: {
  icon: ReactNode;
  sub: string;
  value: number | string;
  label: string;
  accent: string;
}) {
  return (
    <article className="stat-card" style={{ '--accent': accent } as React.CSSProperties}>
      <div className="stat-top">
        <span className="stat-icon">{icon}</span>
        <span className="stat-sub">{sub}</span>
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </article>
  );
}
