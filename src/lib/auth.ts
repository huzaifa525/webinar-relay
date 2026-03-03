import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { verifySession } from './session';
import { redis } from './redis';
import { hashPassword } from './utils';
import { prisma } from './db';
import type { SessionData, UserType } from '@/types';

export async function getSessionFromCookies(): Promise<{
  session: SessionData;
  token: string;
} | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get('session_token')?.value;
  if (!token) return null;

  const session = await verifySession(token);
  if (!session) return null;

  return { session, token };
}

export async function requireSession(allowedType?: UserType): Promise<{
  session: SessionData;
  token: string;
}> {
  const result = await getSessionFromCookies();
  if (!result) redirect('/');
  if (allowedType && result.session.user_type !== allowedType) redirect('/');
  return result;
}

export async function getAdminSession(): Promise<boolean> {
  const cookieStore = await cookies();
  const adminToken = cookieStore.get('admin_session')?.value;
  if (!adminToken) return false;

  const data = await redis.get(`admin_sessions:${adminToken}`);
  return !!data;
}

export async function requireAdmin(): Promise<void> {
  const isAdmin = await getAdminSession();
  if (!isAdmin) redirect('/admin/login');
}

export async function verifyAdminCredentials(
  username: string,
  password: string
): Promise<boolean> {
  const hashedPassword = hashPassword(password);

  const admin = await prisma.adminCredential.findUnique({
    where: { username },
  });

  if (!admin) return false;
  return admin.passwordHash === hashedPassword;
}
