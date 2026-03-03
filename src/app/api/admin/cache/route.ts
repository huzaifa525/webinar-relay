import { NextRequest, NextResponse } from 'next/server';
import { redis } from '@/lib/redis';
import { refreshRedisCache } from '@/lib/cache';

async function verifyAdmin(request: NextRequest): Promise<boolean> {
  const adminToken = request.cookies.get('admin_session')?.value;
  if (!adminToken) return false;
  const data = await redis.get(`admin_sessions:${adminToken}`);
  return !!data;
}

// POST - Refresh Redis cache from database
export async function POST(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    await refreshRedisCache();
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Cache refresh error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to refresh cache' },
      { status: 500 }
    );
  }
}
