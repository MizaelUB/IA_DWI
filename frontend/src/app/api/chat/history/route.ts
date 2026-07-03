import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const { search } = new URL(request.url);
  const res = await fetch(`${FASTAPI_URL}/api/chat/history${search}`);
  const data = await res.json();
  return NextResponse.json(data);
}

export async function DELETE(request: NextRequest) {
  const { search } = new URL(request.url);
  const res = await fetch(`${FASTAPI_URL}/api/chat/history${search}`, { method: 'DELETE' });
  const data = await res.json();
  return NextResponse.json(data);
}
