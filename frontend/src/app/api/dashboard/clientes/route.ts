import { NextRequest, NextResponse } from 'next/server';
import { getJwtFromRequest } from '@/lib/serverAuth';

export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const { token, payload } = getJwtFromRequest(request);
  if (!token) {
    return NextResponse.json({ error: 'No autorizado - Token de autenticación requerido' }, { status: 401 });
  }

  // Prevención IDOR: La validación real de los permisos y el token
  // ocurre en el backend FastAPI de manera segura (con firma JWT verificada).

  // Prevención IDOR: Eliminar parámetro externo y delegar al token en backend
  const { searchParams } = new URL(request.url);
  const page = searchParams.get('page') || '1';
  const limit = searchParams.get('limit') || '10';
  const url = `${FASTAPI_URL}/api/dashboard/clientes?page=${page}&limit=${limit}`;

  try {
    const res = await fetch(url, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'X-Forwarded-For': request.ip || request.headers.get('x-forwarded-for') || ''
      },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json({ error: 'Error al conectar con backend' }, { status: 500 });
  }
}

