import { NextRequest } from 'next/server';

export interface JwtPayload {
  sub?: string;
  veterinary_id?: number;
  user_id?: number;
  type?: string;
  exp?: number;
}

export function getJwtFromRequest(request: NextRequest): { token: string | null; payload: JwtPayload | null } {
  const cookieToken = request.cookies.get('accessToken')?.value;
  let token = cookieToken || null;

  if (!token) {
    const authHeader = request.headers.get('Authorization');
    if (authHeader && authHeader.startsWith('Bearer ')) {
      token = authHeader.substring(7);
    }
  }

  if (!token) {
    return { token: null, payload: null };
  }

  // Se elimina el parseo inseguro del payload (base64) en el frontend.
  // La validación real de la firma (HS256) y extracción de claims 
  // ocurre de forma segura en el backend FastAPI usando la SECRET_KEY.
  return { token, payload: null };
}
