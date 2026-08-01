import type { Cita, Mascota, Cliente, Veterinaria, LoginResponse, ChatHistoryResponse, RegisterRequest } from './types';

const BASE = '';

export async function login(username: string, password: string, captchaId?: string, captchaAnswer?: string): Promise<LoginResponse & { detail?: any }> {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, captcha_id: captchaId, captcha_answer: captchaAnswer }),
  });
  return res.json();
}

export async function fetchVeterinarias(): Promise<Veterinaria[]> {
  const res = await fetch(`${BASE}/api/dashboard/veterinarias`);
  const data = await res.json();
  if (data.status === 'success' && Array.isArray(data.data)) return data.data;
  return [];
}

export async function fetchCitas(vetId?: string): Promise<Cita[]> {
  const param = vetId ? `?veterinary_id=${vetId}` : '';
  const res = await fetch(`${BASE}/api/dashboard/citas${param}`);
  const data = await res.json();
  if (data.status === 'success' && Array.isArray(data.data)) return data.data;
  return [];
}

export async function fetchMascotas(vetId?: string): Promise<Mascota[]> {
  const param = vetId ? `?veterinary_id=${vetId}` : '';
  const res = await fetch(`${BASE}/api/dashboard/mascotas${param}`);
  const data = await res.json();
  if (data.status === 'success' && Array.isArray(data.data)) return data.data;
  return [];
}
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    total_pages: number;
  };
}

export async function fetchClientes(vetId?: string, page: number = 1, limit: number = 10): Promise<PaginatedResponse<Cliente>> {
  const param = vetId ? `?veterinary_id=${vetId}&page=${page}&limit=${limit}` : `?page=${page}&limit=${limit}`;
  const res = await fetch(`${BASE}/api/dashboard/clientes${param}`);
  const data = await res.json();
  if (data.status === 'success' && data.pagination) return { data: data.data, pagination: data.pagination };
  return { data: [], pagination: { total: 0, page: 1, limit, total_pages: 1 } };
}

export async function loginGuest(): Promise<LoginResponse> {
  const res = await fetch(`${BASE}/api/auth/guest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  return res.json();
}

export async function fetchChatHistory(): Promise<ChatHistoryResponse> {
  const res = await fetch(`${BASE}/api/chat/history`);
  return res.json();
}

export async function deleteChatHistory(): Promise<void> {
  await fetch(`${BASE}/api/chat/history`, { method: 'DELETE' });
}

export async function register(data: RegisterRequest): Promise<LoginResponse & { detail?: any; message?: string }> {
  const res = await fetch(`${BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}
