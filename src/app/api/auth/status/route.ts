import { NextRequest, NextResponse } from 'next/server';
import { verifySession } from '@/lib/session';

export async function GET(request: NextRequest) {
  const token = request.cookies.get('session_token')?.value;

  if (!token) {
    return NextResponse.json({ logged_in: false });
  }

  const session = await verifySession(token);

  if (!session) {
    return NextResponse.json({ logged_in: false });
  }

  return NextResponse.json({
    logged_in: true,
    user_id: session.user_id,
    user_type: session.user_type,
    login_time: session.login_time,
  });
}
