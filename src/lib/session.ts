import { redis, KEYS, TTL } from './redis';
import { generateSessionToken } from './utils';
import { wsEvents } from './websocket';
import type { SessionData, UserType } from '@/types';

export async function createSession(userId: string, userType: UserType): Promise<string> {
  const token = generateSessionToken();
  const sessionData: SessionData = {
    user_type: userType,
    user_id: userId,
    login_time: new Date().toISOString(),
    last_activity: new Date().toISOString(),
  };

  await redis.setex(
    KEYS.session(token),
    TTL.session,
    JSON.stringify(sessionData)
  );

  // Emit WebSocket event for real-time updates
  wsEvents.emit('user_connected', { user_id: userId, user_type: userType });

  return token;
}

export async function verifySession(token: string): Promise<SessionData | null> {
  const data = await redis.get(KEYS.session(token));
  if (!data) return null;

  const session: SessionData = JSON.parse(data);

  // Update last activity and reset TTL
  session.last_activity = new Date().toISOString();
  await redis.setex(KEYS.session(token), TTL.session, JSON.stringify(session));

  return session;
}

export async function logoutSession(token: string): Promise<boolean> {
  // Get session data before deleting to emit event
  const data = await redis.get(KEYS.session(token));
  const result = await redis.del(KEYS.session(token));

  if (result > 0 && data) {
    const session: SessionData = JSON.parse(data);
    wsEvents.emit('user_disconnected', { user_id: session.user_id, user_type: session.user_type });
  }

  return result > 0;
}

export async function getAllSessions(): Promise<Record<string, SessionData>> {
  const sessions: Record<string, SessionData> = {};
  let cursor = '0';

  do {
    const [nextCursor, keys] = await redis.scan(cursor, 'MATCH', 'sessions:*', 'COUNT', 100);
    cursor = nextCursor;

    if (keys.length > 0) {
      const values = await Promise.all(keys.map(k => redis.get(k)));
      for (let i = 0; i < keys.length; i++) {
        if (values[i]) {
          const token = keys[i].replace('sessions:', '');
          sessions[token] = JSON.parse(values[i]!);
        }
      }
    }
  } while (cursor !== '0');

  return sessions;
}

export async function clearAllSessions(): Promise<boolean> {
  let cursor = '0';
  const keys: string[] = [];

  do {
    const [nextCursor, foundKeys] = await redis.scan(cursor, 'MATCH', 'sessions:*', 'COUNT', 100);
    cursor = nextCursor;
    keys.push(...foundKeys);
  } while (cursor !== '0');

  if (keys.length > 0) {
    await redis.del(...keys);
  }
  return true;
}

export async function isUserAlreadyLoggedIn(userId: string, userType: UserType): Promise<boolean> {
  const sessions = await getAllSessions();
  return Object.values(sessions).some(
    (s) => s.user_id === userId && s.user_type === userType
  );
}

export async function removeExistingUserSessions(userId: string, userType: UserType): Promise<number> {
  const sessions = await getAllSessions();
  const matchingTokens = Object.entries(sessions)
    .filter(([, session]) => session.user_id === userId && session.user_type === userType)
    .map(([token]) => token);

  if (matchingTokens.length > 0) {
    await Promise.all(matchingTokens.map(token => redis.del(KEYS.session(token))));
  }

  return matchingTokens.length;
}

export async function updateUserActivity(userId: string, userType: string): Promise<void> {
  await redis.setex(
    KEYS.activity(userId, userType),
    TTL.activity,
    new Date().toISOString()
  );
}

export async function getUserLastActivity(userId: string, userType: string): Promise<string | null> {
  return redis.get(KEYS.activity(userId, userType));
}
