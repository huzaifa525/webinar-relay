import { NextRequest, NextResponse } from 'next/server';
import { redis } from '@/lib/redis';

export async function POST(request: NextRequest) {
  const adminToken = request.cookies.get('admin_session')?.value;

  if (adminToken) {
    await redis.del(`admin_sessions:${adminToken}`);
  }

  const response = NextResponse.json({ success: true });
  response.cookies.delete('admin_session');

  return response;
}
