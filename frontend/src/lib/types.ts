export interface Cita {
  id: number;
  mascota: string;
  fecha: string;
  hora: string;
  estado: string;
  dueno: string;
  veterinaria: string;
  notas?: string;
}

export interface Mascota {
  id: number;
  nombre: string;
  especie: string;
  raza: string;
  dueno: string;
  citas?: Array<{
    id: number;
    fecha: string;
    hora: string;
    estado: string;
    notas?: string;
  }>;
}

export interface Cliente {
  id: number;
  nombre: string;
  telefono: string;
  email: string;
}

export interface Veterinaria {
  id: number;
  name: string;
  city: string;
}

export interface Session {
  username: string;
  veterinary_id: number | null;
  veterinary_name: string;
  user_id?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'bot';
  content: string;
  isMarkdown?: boolean;
  isStreaming?: boolean;
}

export interface ChatHistoryResponse {
  conversation_id: string | null;
  history: Array<{ role: string; content: string }>;
}

export interface LoginResponse {
  status: string;
  username: string;
  veterinary_id: number | null;
  veterinary_name: string;
  user_id?: number;
  access_token?: string;
  token_type?: string;
  detail?: string;
  message?: string;
}

export interface RegisterRequest {
  username?: string;
  password: string;
  email: string;
  full_name: string;
  phone: string;
  doctor_license: string;
  vet_name: string;
  vet_city: string;
  vet_address?: string;
  vet_phone?: string;
  vet_email?: string;
}
