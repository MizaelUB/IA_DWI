import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const res = await fetch(`${FASTAPI_URL}/api/auth/reset-password-code`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-Forwarded-For': request.ip || request.headers.get('x-forwarded-for') || ''
      },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      console.error('FastAPI returned non-JSON response:', text);
      return NextResponse.json({ status: 'error', detail: 'Respuesta inválida del servidor' }, { status: res.status });
    }
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json({ status: 'error', detail: 'Error al conectar con backend' }, { status: 500 });
  }
}
