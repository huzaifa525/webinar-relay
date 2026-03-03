import Redis from 'ioredis';

const globalForRedis = globalThis as unknown as {
  redis: Redis | undefined;
};

function createRedisClient(): Redis {
  const url = process.env.REDIS_URL;
  if (!url) {
    throw new Error('REDIS_URL environment variable is required');
  }

  return new Redis(url, {
    maxRetriesPerRequest: 3,
    retryStrategy(times) {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
    enableReadyCheck: true,
    connectTimeout: 5000,
  });
}

export const redis = globalForRedis.redis ?? createRedisClient();

if (process.env.NODE_ENV !== 'production') globalForRedis.redis = redis;

// Key constants
export const KEYS = {
  session: (token: string) => `sessions:${token}`,
  itsIds: 'cached:its_ids',
  majlisIds: 'cached:majlis_ids',
  webinarSettings: 'cached:webinar_settings',
  majlisSettings: 'cached:majlis_settings',
  activity: (userId: string, userType: string) => `activity:${userId}:${userType}`,
} as const;

// TTL constants (in seconds)
export const TTL = {
  session: 86400,       // 24 hours
  activity: 7200,       // 2 hours
  adminSession: 86400,  // 24 hours
} as const;
