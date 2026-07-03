import { estadoKey, estadoLabel } from '@/lib/utils';

export function StatusBadge({ estado }: { estado: string }) {
  const key = estadoKey(estado);
  return <span className={`status-badge ${key}`}>{estadoLabel(estado)}</span>;
}
