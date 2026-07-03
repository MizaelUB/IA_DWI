const AV_COLORS: [string, string][] = [
  ['#D9663C', '#A8461F'], ['#B5512F', '#7A3520'], ['#E89A2F', '#B06A1F'],
  ['#5E9B86', '#3F6B5A'], ['#C2552E', '#8A3A1A'], ['#8A6E5A', '#5A4636'],
  ['#A8743E', '#6E4A23'], ['#6E8A5A', '#465A38'],
];

export function avColor(name: string): [string, string] {
  let h = 0;
  const s = String(name || '?');
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return AV_COLORS[h % AV_COLORS.length];
}

export function initials(name: string): string {
  const s = String(name || '?').trim();
  const parts = s.split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return s.slice(0, 2).toUpperCase();
}

export function avatarGradient(name: string): string {
  const [a, b] = avColor(name);
  return `linear-gradient(150deg, ${a}, ${b})`;
}

export function escapeHtml(s: unknown): string {
  return String(s == null ? '' : s).replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string),
  );
}

export function parseFecha(f: string | null | undefined): Date | null {
  if (!f) return null;
  const s = String(f).trim();
  let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m) return new Date(+m[1], +m[2] - 1, +m[3]);
  m = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/);
  if (m) return new Date(+m[3], +m[2] - 1, +m[1]);
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
}

export function startOfDay(d: Date): Date {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

export function sameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

export function padTime(t: string): string {
  if (!t) return '';
  const p = String(t).split(':');
  if (p.length < 2) return String(t);
  return p[0].padStart(2, '0') + ':' + p[1].padStart(2, '0');
}

export function fmtDate(d: Date): string {
  return String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0');
}

export const WD = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
export const WD_FULL = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];

export type EstadoKey = 'pendiente' | 'confirmada' | 'cancelada' | 'atendida';

export function estadoKey(estado: string): EstadoKey {
  const e = String(estado || '').toLowerCase();
  if (e.includes('cancel')) return 'cancelada';
  if (e.includes('pend')) return 'pendiente';
  if (e.includes('confirm')) return 'confirmada';
  if (e.includes('atend') || e.includes('complet') || e.includes('final')) return 'atendida';
  return 'pendiente';
}

export function estadoLabel(estado: string): string {
  const e = String(estado || '').toLowerCase();
  if (e.includes('cancel')) return 'Cancelada';
  if (e.includes('pend')) return 'Pendiente';
  if (e.includes('confirm')) return 'Confirmada';
  if (e.includes('atend') || e.includes('complet') || e.includes('final')) return 'Atendida';
  return escapeHtml(estado || '—');
}
