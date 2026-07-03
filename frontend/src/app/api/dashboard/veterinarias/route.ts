import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function GET() {
  const res = await fetch(`${FASTAPI_URL}/api/dashboard/veterinarias`);
  const data = await res.json();
  return NextResponse.json(data);
}
