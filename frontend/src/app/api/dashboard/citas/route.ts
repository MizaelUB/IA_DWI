import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const vetId = searchParams.get('veterinary_id');
  const url = vetId
    ? `${FASTAPI_URL}/api/dashboard/citas?veterinary_id=${vetId}`
    : `${FASTAPI_URL}/api/dashboard/citas`;
  const res = await fetch(url);
  const data = await res.json();
  return NextResponse.json(data);
}
