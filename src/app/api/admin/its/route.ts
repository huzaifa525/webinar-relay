import { NextRequest, NextResponse } from 'next/server';
import { redis } from '@/lib/redis';
import { getAllItsIds, saveItsId, deleteItsId, deleteAllItsIds } from '@/lib/cache';
import { removeExistingUserSessions } from '@/lib/session';
import { isValidId } from '@/lib/utils';

async function verifyAdmin(request: NextRequest): Promise<boolean> {
  const adminToken = request.cookies.get('admin_session')?.value;
  if (!adminToken) return false;
  const data = await redis.get(`admin_sessions:${adminToken}`);
  return !!data;
}

// GET - List all ITS IDs
export async function GET(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const ids = await getAllItsIds();
  return NextResponse.json({ ids, count: ids.length });
}

// POST - Add ITS ID(s)
export async function POST(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const { action, id, ids: bulkIdsStr } = body;

  if (action === 'bulk_add') {
    // Parse comma/newline separated IDs
    const rawIds = (bulkIdsStr as string)
      .split(/[\s,]+/)
      .map((s: string) => s.trim())
      .filter((s: string) => isValidId(s));

    if (rawIds.length === 0) {
      return NextResponse.json({ success: false, error: 'No valid 8-digit IDs found' }, { status: 400 });
    }

    let added = 0;
    for (const rawId of rawIds) {
      if (await saveItsId(rawId)) added++;
    }

    return NextResponse.json({ success: true, count: added });
  }

  // Single add
  if (!id || !isValidId(id)) {
    return NextResponse.json({ success: false, error: 'Invalid 8-digit ID' }, { status: 400 });
  }

  const saved = await saveItsId(id);
  if (!saved) {
    return NextResponse.json({ success: false, error: 'ID already exists or save failed' }, { status: 409 });
  }

  return NextResponse.json({ success: true });
}

// DELETE - Delete ITS ID(s)
export async function DELETE(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const { action, id } = body;

  if (action === 'delete_all') {
    await deleteAllItsIds();
    return NextResponse.json({ success: true });
  }

  if (!id) {
    return NextResponse.json({ success: false, error: 'ID required' }, { status: 400 });
  }

  const deleted = await deleteItsId(id);
  if (deleted) {
    // Force logout any sessions for this ID
    await removeExistingUserSessions(id, 'its');
  }

  return NextResponse.json({ success: deleted });
}
