import type { Cita, Mascota, Cliente, Veterinaria, LoginResponse, ChatHistoryResponse } from './types';

const BASE = '';

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
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

export async function fetchClientes(vetId?: string): Promise<Cliente[]> {
  const param = vetId ? `?veterinary_id=${vetId}` : '';
  const res = await fetch(`${BASE}/api/dashboard/clientes${param}`);
  const data = await res.json();
  if (data.status === 'success' && Array.isArray(data.data)) return data.data;
  return [];
}

export async function fetchChatHistory(conversationId?: string | null, vetId?: number | null, userId?: number | null): Promise<ChatHistoryResponse> {
  let query = '';
  if (conversationId) {
    query = `?conversation_id=${encodeURIComponent(conversationId)}`;
    if (userId) query += `&user_id=${userId}`;
  } else if (vetId) {
    query = `?veterinary_id=${vetId}&user_id=${userId || 1}`;
  }
  const res = await fetch(`${BASE}/api/chat/history${query}`);
  return res.json();
}

export async function deleteChatHistory(conversationId?: string | null, vetId?: number | null, userId?: number | null): Promise<void> {
  let query = '';
  if (conversationId) {
    query = `?conversation_id=${encodeURIComponent(conversationId)}`;
    if (userId) query += `&user_id=${userId}`;
  } else if (vetId) {
    query = `?veterinary_id=${vetId}&user_id=${userId || 1}`;
  }
  await fetch(`${BASE}/api/chat/history${query}`, { method: 'DELETE' });
}
