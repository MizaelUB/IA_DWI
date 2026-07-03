'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import type { Cita, Mascota, Cliente, Veterinaria } from '@/lib/types';
import { fetchVeterinarias, fetchCitas, fetchMascotas, fetchClientes } from '@/lib/api';
import { useAuth } from './AuthContext';

interface DashboardContextType {
  citas: Cita[];
  mascotas: Mascota[];
  clientes: Cliente[];
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
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [veterinarias, setVeterinarias] = useState<Veterinaria[]>([]);
  const [selectedVetId, setSelectedVetId] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    const vetId = selectedVetId || undefined;
    const [c, m, cl] = await Promise.all([
      fetchCitas(vetId),
      fetchMascotas(vetId),
      fetchClientes(vetId),
    ]);
    setCitas(c);
    setMascotas(m);
    setClientes(cl);
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
      value={{ citas, mascotas, clientes, veterinarias, selectedVetId, setSelectedVetId, isLoading, refresh }}
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
