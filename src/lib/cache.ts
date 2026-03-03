import { redis, KEYS } from './redis';
import { prisma } from './db';
import { buildEmbedUrl } from './utils';
import { wsEvents } from './websocket';
import type { WebinarSettings, UserType } from '@/types';

// --- ID Validation ---

export async function isItsIdValid(id: string): Promise<boolean> {
  return (await redis.sismember(KEYS.itsIds, id)) === 1;
}

export async function isMajlisIdValid(id: string): Promise<boolean> {
  return (await redis.sismember(KEYS.majlisIds, id)) === 1;
}

// --- ID Management ---

export async function saveItsId(id: string): Promise<boolean> {
  try {
    await prisma.itsId.create({ data: { id } });
    await redis.sadd(KEYS.itsIds, id);
    wsEvents.emit('ids_updated', { type: 'its', action: 'add', id });
    return true;
  } catch {
    return false;
  }
}

export async function saveMajlisId(id: string): Promise<boolean> {
  try {
    await prisma.majlisId.create({ data: { id } });
    await redis.sadd(KEYS.majlisIds, id);
    wsEvents.emit('ids_updated', { type: 'majlis', action: 'add', id });
    return true;
  } catch {
    return false;
  }
}

export async function deleteItsId(id: string): Promise<boolean> {
  try {
    await prisma.itsId.delete({ where: { id } });
    await redis.srem(KEYS.itsIds, id);
    wsEvents.emit('ids_updated', { type: 'its', action: 'delete', id });
    return true;
  } catch {
    return false;
  }
}

export async function deleteMajlisId(id: string): Promise<boolean> {
  try {
    await prisma.majlisId.delete({ where: { id } });
    await redis.srem(KEYS.majlisIds, id);
    wsEvents.emit('ids_updated', { type: 'majlis', action: 'delete', id });
    return true;
  } catch {
    return false;
  }
}

export async function deleteAllItsIds(): Promise<boolean> {
  try {
    await prisma.itsId.deleteMany();
    await redis.del(KEYS.itsIds);
    wsEvents.emit('ids_updated', { type: 'its', action: 'delete_all' });
    return true;
  } catch {
    return false;
  }
}

export async function deleteAllMajlisIds(): Promise<boolean> {
  try {
    await prisma.majlisId.deleteMany();
    await redis.del(KEYS.majlisIds);
    wsEvents.emit('ids_updated', { type: 'majlis', action: 'delete_all' });
    return true;
  } catch {
    return false;
  }
}

export async function getAllItsIds(): Promise<string[]> {
  const ids = await redis.smembers(KEYS.itsIds);
  if (ids.length > 0) return ids.sort();

  // Fallback to database
  const dbIds = await prisma.itsId.findMany({ select: { id: true } });
  const idList = dbIds.map((i) => i.id);
  if (idList.length > 0) {
    await redis.sadd(KEYS.itsIds, ...idList);
  }
  return idList.sort();
}

export async function getAllMajlisIds(): Promise<string[]> {
  const ids = await redis.smembers(KEYS.majlisIds);
  if (ids.length > 0) return ids.sort();

  // Fallback to database
  const dbIds = await prisma.majlisId.findMany({ select: { id: true } });
  const idList = dbIds.map((i) => i.id);
  if (idList.length > 0) {
    await redis.sadd(KEYS.majlisIds, ...idList);
  }
  return idList.sort();
}

// --- Webinar Settings ---

const DEFAULT_ITS_SETTINGS: WebinarSettings = {
  embed_url: buildEmbedUrl('GXRL7PcPbOA'),
  youtube_video_id: 'GXRL7PcPbOA',
  webinar_title: 'Ashara Mubaraka 1447 - Ratlam Relay (ITS)',
  no_webinar: false,
};

const DEFAULT_MAJLIS_SETTINGS: WebinarSettings = {
  embed_url: buildEmbedUrl('GXRL7PcPbOA'),
  youtube_video_id: 'GXRL7PcPbOA',
  webinar_title: 'Ashara Mubaraka 1447 - Ratlam Relay (Majlis)',
  no_webinar: false,
};

export async function loadWebinarSettings(type: UserType = 'its'): Promise<WebinarSettings> {
  const cacheKey = type === 'its' ? KEYS.webinarSettings : KEYS.majlisSettings;
  const defaults = type === 'its' ? DEFAULT_ITS_SETTINGS : DEFAULT_MAJLIS_SETTINGS;

  try {
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);
  } catch {
    // Fallback below
  }

  try {
    const setting = type === 'its'
      ? await prisma.webinarSetting.findFirst()
      : await prisma.majlisWebinarSetting.findFirst();

    if (setting) {
      const result: WebinarSettings = {
        embed_url: buildEmbedUrl(setting.youtubeVideoId),
        youtube_video_id: setting.youtubeVideoId,
        webinar_title: setting.webinarTitle,
        no_webinar: setting.noWebinar ?? false,
      };

      await redis.set(cacheKey, JSON.stringify(result));
      return result;
    }
  } catch (e) {
    console.error(`Error loading ${type} settings from database:`, e);
  }

  return defaults;
}

export function isWebinarTimeActive(settings: WebinarSettings): boolean {
  return !settings.no_webinar;
}

export async function loadWebinarSettingsWithTimeCheck(type: UserType = 'its'): Promise<WebinarSettings> {
  return loadWebinarSettings(type);
}

// --- Cache Refresh ---

export async function refreshRedisCache(): Promise<void> {
  const [itsIds, majlisIds, itsSetting, majlisSetting] = await Promise.all([
    prisma.itsId.findMany({ select: { id: true } }),
    prisma.majlisId.findMany({ select: { id: true } }),
    prisma.webinarSetting.findFirst(),
    prisma.majlisWebinarSetting.findFirst(),
  ]);

  const writes: Promise<unknown>[] = [
    redis.del(KEYS.itsIds).then(() =>
      itsIds.length > 0 ? redis.sadd(KEYS.itsIds, ...itsIds.map(i => i.id)) : Promise.resolve(0)
    ),
    redis.del(KEYS.majlisIds).then(() =>
      majlisIds.length > 0 ? redis.sadd(KEYS.majlisIds, ...majlisIds.map(i => i.id)) : Promise.resolve(0)
    ),
  ];

  if (itsSetting) {
    writes.push(redis.set(KEYS.webinarSettings, JSON.stringify({
      embed_url: buildEmbedUrl(itsSetting.youtubeVideoId),
      youtube_video_id: itsSetting.youtubeVideoId,
      webinar_title: itsSetting.webinarTitle,
      no_webinar: itsSetting.noWebinar ?? false,
    })));
  }

  if (majlisSetting) {
    writes.push(redis.set(KEYS.majlisSettings, JSON.stringify({
      embed_url: buildEmbedUrl(majlisSetting.youtubeVideoId),
      youtube_video_id: majlisSetting.youtubeVideoId,
      webinar_title: majlisSetting.webinarTitle,
      no_webinar: majlisSetting.noWebinar ?? false,
    })));
  }

  await Promise.all(writes);
}
