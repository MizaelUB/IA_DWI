import { ReactNode } from 'react';

export function EmptyState({
  icon,
  title,
  subtitle,
}: {
  icon: ReactNode;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="table-empty">
      <span className="empty-icon">{icon}</span>
      <p className="empty-title">{title}</p>
      <p className="empty-sub">{subtitle}</p>
    </div>
  );
}
