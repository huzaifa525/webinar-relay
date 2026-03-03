import { NextRequest, NextResponse } from 'next/server';
import { logoutSession } from '@/lib/session';

export async function POST(request: NextRequest) {
  const token = request.cookies.get('session_token')?.value;

  if (token) {
    await logoutSession(token);
  }

  const response = NextResponse.json({ success: true });
  response.cookies.delete('session_token');

  return response;
}
