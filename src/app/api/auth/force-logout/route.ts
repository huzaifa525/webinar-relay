import { NextRequest, NextResponse } from 'next/server';
import { verifySession, removeExistingUserSessions } from '@/lib/session';

export async function POST(request: NextRequest) {
  const token = request.cookies.get('session_token')?.value;

  if (token) {
    const session = await verifySession(token);
    if (session) {
      await removeExistingUserSessions(session.user_id, session.user_type);
    }
  }

  const response = NextResponse.json({ success: true });
  response.cookies.delete('session_token');

  return response;
}
