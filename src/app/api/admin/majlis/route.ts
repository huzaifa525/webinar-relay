import { NextRequest, NextResponse } from 'next/server';
import { redis } from '@/lib/redis';
import { getAllMajlisIds, saveMajlisId, deleteMajlisId, deleteAllMajlisIds } from '@/lib/cache';
import { removeExistingUserSessions } from '@/lib/session';
import { isValidId } from '@/lib/utils';

async function verifyAdmin(request: NextRequest): Promise<boolean> {
  const adminToken = request.cookies.get('admin_session')?.value;
  if (!adminToken) return false;
  const data = await redis.get(`admin_sessions:${adminToken}`);
  return !!data;
}

// GET - List all Majlis IDs
export async function GET(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const ids = await getAllMajlisIds();
  return NextResponse.json({ ids, count: ids.length });
}

// POST - Add Majlis ID(s)
export async function POST(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const { action, id, ids: bulkIdsStr } = body;

  if (action === 'bulk_add') {
    const rawIds = (bulkIdsStr as string)
      .split(/[\s,]+/)
      .map((s: string) => s.trim())
      .filter((s: string) => isValidId(s));

    if (rawIds.length === 0) {
      return NextResponse.json({ success: false, error: 'No valid 8-digit IDs found' }, { status: 400 });
    }

    let added = 0;
    for (const rawId of rawIds) {
      if (await saveMajlisId(rawId)) added++;
    }

    return NextResponse.json({ success: true, count: added });
  }

  if (!id || !isValidId(id)) {
    return NextResponse.json({ success: false, error: 'Invalid 8-digit ID' }, { status: 400 });
  }

  const saved = await saveMajlisId(id);
  if (!saved) {
    return NextResponse.json({ success: false, error: 'ID already exists or save failed' }, { status: 409 });
  }

  return NextResponse.json({ success: true });
}

// DELETE - Delete Majlis ID(s)
export async function DELETE(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const { action, id } = body;

  if (action === 'delete_all') {
    await deleteAllMajlisIds();
    return NextResponse.json({ success: true });
  }

  if (!id) {
    return NextResponse.json({ success: false, error: 'ID required' }, { status: 400 });
  }

  const deleted = await deleteMajlisId(id);
  if (deleted) {
    await removeExistingUserSessions(id, 'majlis');
  }

  return NextResponse.json({ success: deleted });
}
