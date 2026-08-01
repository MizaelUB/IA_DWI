import { NextRequest, NextResponse } from 'next/server';
import { getJwtFromRequest } from '@/lib/serverAuth';

export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const { token } = getJwtFromRequest(request);
  if (token) {
    try {
      await fetch(`${FASTAPI_URL}/api/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (e) {
      console.error("Logout backend error", e);
    }
  }

  const response = NextResponse.json({ success: true });
  response.cookies.set('accessToken', '', { path: '/', expires: new Date(0) });
  return response;
}
