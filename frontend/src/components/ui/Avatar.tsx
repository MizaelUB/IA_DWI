import { initials, avatarGradient } from '@/lib/utils';

export function Avatar({ name, size = 38 }: { name: string; size?: number }) {
  return (
    <span
      className="avatar"
      style={{ width: size, height: size, background: avatarGradient(name) }}
    >
      {initials(name)}
    </span>
  );
}

export function PatientAvatar({ name, size = 46 }: { name: string; size?: number }) {
  return (
    <span
      className="patient-avatar"
      style={{ width: size, height: size, background: avatarGradient(name) }}
    >
      {initials(name)}
    </span>
  );
}

export function PetAvatar({ name, size = 32 }: { name: string; size?: number }) {
  return (
    <span
      className="pet-avatar"
      style={{ width: size, height: size, background: avatarGradient(name) }}
    >
      {initials(name)}
    </span>
  );
}
