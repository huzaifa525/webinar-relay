import { NextRequest, NextResponse } from 'next/server';
import { redis } from '@/lib/redis';
import { getAllSessions, logoutSession, removeExistingUserSessions, clearAllSessions } from '@/lib/session';
import { getAllItsIds, getAllMajlisIds } from '@/lib/cache';

async function verifyAdmin(request: NextRequest): Promise<boolean> {
  const adminToken = request.cookies.get('admin_session')?.value;
  if (!adminToken) return false;
  const data = await redis.get(`admin_sessions:${adminToken}`);
  return !!data;
}

// GET - List sessions or get stats
export async function GET(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action');

  if (action === 'stats') {
    const sessions = await getAllSessions();
    const sessionList = Object.values(sessions);
    const itsIds = await getAllItsIds();
    const majlisIds = await getAllMajlisIds();

    return NextResponse.json({
      total_its: itsIds.length,
      total_majlis: majlisIds.length,
      its_sessions: sessionList.filter((s) => s.user_type === 'its').length,
      majlis_sessions: sessionList.filter((s) => s.user_type === 'majlis').length,
      total_sessions: sessionList.length,
    });
  }

  // List all sessions
  const sessions = await getAllSessions();
  const sessionList = Object.entries(sessions).map(([token, data]) => ({
    token,
    user_id: data.user_id,
    user_type: data.user_type,
    login_time: data.login_time,
    last_activity: data.last_activity,
  }));

  return NextResponse.json({ sessions: sessionList });
}

// DELETE - Manage sessions
export async function DELETE(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const { action, token, user_id, user_type } = body;

  switch (action) {
    case 'kick':
      if (!token) {
        return NextResponse.json({ success: false, error: 'Token required' }, { status: 400 });
      }
      await logoutSession(token);
      return NextResponse.json({ success: true });

    case 'force_logout':
      if (!user_id || !user_type) {
        return NextResponse.json({ success: false, error: 'user_id and user_type required' }, { status: 400 });
      }
      const count = await removeExistingUserSessions(user_id, user_type);
      return NextResponse.json({ success: true, removed: count });

    case 'clear_all':
      await clearAllSessions();
      return NextResponse.json({ success: true });

    default:
      return NextResponse.json({ success: false, error: 'Invalid action' }, { status: 400 });
  }
}
