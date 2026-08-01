import { NextRequest, NextResponse } from 'next/server';

import { getJwtFromRequest } from '@/lib/serverAuth';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { token } = getJwtFromRequest(request);

  const headers: Record<string, string> = { 
    'Content-Type': 'application/json',
    'X-Forwarded-For': request.ip || request.headers.get('x-forwarded-for') || ''
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${FASTAPI_URL}/api/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (res.status === 429) {
    const errBody = await res.json().catch(() => ({}));
    return NextResponse.json(errBody, { status: 429 });
  }

  const convId = res.headers.get('X-Conversation-Id');

  return new Response(res.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      ...(convId ? { 'X-Conversation-Id': convId } : {}),
    },
  });
}
