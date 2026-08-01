import { NextRequest, NextResponse } from 'next/server';
import { getJwtFromRequest } from '@/lib/serverAuth';

export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const { token, payload } = getJwtFromRequest(request);
  if (!token) {
    return NextResponse.json({ error: 'No autorizado - Token de autenticación requerido' }, { status: 401 });
  }

  // La extracción y validación de user_id/veterinary_id
  // se realiza de forma 100% segura en el backend a partir del JWT.

  try {
    const res = await fetch(`${FASTAPI_URL}/api/chat/history${new URL(request.url).search}`, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'X-Forwarded-For': request.ip || request.headers.get('x-forwarded-for') || ''
      }
    });
    const contentType = res.headers.get('content-type');
    let data = {};
    if (contentType && contentType.includes('application/json')) {
      data = await res.json();
    } else {
      console.error('Non-JSON response in GET:', await res.text());
      return NextResponse.json({ error: 'Backend error' }, { status: res.status || 500 });
    }
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    console.error('Error fetching chat history:', err);
    return NextResponse.json({ conversation_id: null, history: [] }, { status: 200 });
  }
}

export async function DELETE(request: NextRequest) {
  const { token, payload } = getJwtFromRequest(request);
  if (!token) {
    return NextResponse.json({ error: 'No autorizado - Token de autenticación requerido' }, { status: 401 });
  }

  // La validación ocurre en el backend.

  try {
    const res = await fetch(`${FASTAPI_URL}/api/chat/history${new URL(request.url).search}`, {
      method: 'DELETE',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'X-Forwarded-For': request.ip || request.headers.get('x-forwarded-for') || ''
      }
    });
    const contentType = res.headers.get('content-type');
    let data = {};
    if (contentType && contentType.includes('application/json')) {
      data = await res.json();
    } else {
      console.error('Non-JSON response in DELETE:', await res.text());
      return NextResponse.json({ error: 'Backend error' }, { status: res.status || 500 });
    }
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    console.error('Error deleting chat history:', err);
    return NextResponse.json({ status: 'success' }, { status: 200 });
  }
}
