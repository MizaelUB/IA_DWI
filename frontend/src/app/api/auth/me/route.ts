import { NextRequest, NextResponse } from 'next/server';
import { getJwtFromRequest } from '@/lib/serverAuth';

export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const { token } = getJwtFromRequest(request);
  if (!token) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 401 });
  }

  try {
    const res = await fetch(`${FASTAPI_URL}/api/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (!res.ok) {
       return NextResponse.json({ error: 'No autorizado' }, { status: res.status });
    }
    const backendPayload = await res.json();
    return NextResponse.json(backendPayload);
  } catch (err) {
    return NextResponse.json({ error: 'Error al conectar con backend' }, { status: 500 });
  }
}
