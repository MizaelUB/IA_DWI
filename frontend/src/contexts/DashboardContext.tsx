'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import type { Cita, Mascota, Cliente, Veterinaria } from '@/lib/types';
import { fetchVeterinarias, fetchCitas, fetchMascotas } from '@/lib/api';
import { useAuth } from './AuthContext';

interface DashboardContextType {
  citas: Cita[];
  mascotas: Mascota[];
  veterinarias: Veterinaria[];
  selectedVetId: string;
  setSelectedVetId: (id: string) => void;
  isLoading: boolean;
  refresh: () => Promise<void>;
}

const DashboardContext = createContext<DashboardContextType | null>(null);

export function DashboardProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [citas, setCitas] = useState<Cita[]>([]);
  const [mascotas, setMascotas] = useState<Mascota[]>([]);
  const [veterinarias, setVeterinarias] = useState<Veterinaria[]>([]);
  const [selectedVetId, setSelectedVetId] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    const vetId = selectedVetId || undefined;
    const [c, m] = await Promise.all([
      fetchCitas(vetId),
      fetchMascotas(vetId),
    ]);
    setCitas(c);
    setMascotas(m);
    setIsLoading(false);
  }, [selectedVetId]);

  useEffect(() => {
    fetchVeterinarias().then(setVeterinarias);
  }, []);

  useEffect(() => {
    if (user) {
      if (user.veterinary_id && !selectedVetId) {
        setSelectedVetId(String(user.veterinary_id));
      } else {
        refresh();
      }
    }
  }, [user, selectedVetId, refresh]);

  return (
    <DashboardContext.Provider
      value={{ citas, mascotas, veterinarias, selectedVetId, setSelectedVetId, isLoading, refresh }}
    >
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard(): DashboardContextType {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error('useDashboard must be used within DashboardProvider');
  return ctx;
}
