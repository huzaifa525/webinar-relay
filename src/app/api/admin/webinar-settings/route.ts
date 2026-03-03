import { NextRequest, NextResponse } from 'next/server';
import { redis, KEYS } from '@/lib/redis';
import { prisma } from '@/lib/db';
import { loadWebinarSettings } from '@/lib/cache';
import { extractYoutubeId, buildEmbedUrl } from '@/lib/utils';
import { wsEvents } from '@/lib/websocket';

async function verifyAdmin(request: NextRequest): Promise<boolean> {
  const adminToken = request.cookies.get('admin_session')?.value;
  if (!adminToken) return false;
  const data = await redis.get(`admin_sessions:${adminToken}`);
  return !!data;
}

// GET - Load ITS webinar settings
export async function GET(request: NextRequest) {
  // Allow both admin and authenticated users to read settings
  const settings = await loadWebinarSettings('its');
  return NextResponse.json(settings);
}

// PUT - Update ITS webinar settings
export async function PUT(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await request.json();
    const {
      youtube_video_id,
      webinar_title,
      webinar_description,
      webinar_date,
      webinar_time,
      webinar_speaker,
      start_time,
      end_time,
      no_webinar,
    } = body;

    const videoId = extractYoutubeId(youtube_video_id || '');

    // Find or create the settings record
    let setting = await prisma.webinarSetting.findFirst();

    if (setting) {
      setting = await prisma.webinarSetting.update({
        where: { id: setting.id },
        data: {
          youtubeVideoId: videoId,
          webinarTitle: webinar_title || setting.webinarTitle,
          webinarDescription: webinar_description || setting.webinarDescription,
          webinarDate: webinar_date || setting.webinarDate,
          webinarTime: webinar_time || setting.webinarTime,
          webinarSpeaker: webinar_speaker || setting.webinarSpeaker,
          startTime: start_time ? new Date(start_time) : null,
          endTime: end_time ? new Date(end_time) : null,
          noWebinar: no_webinar ?? false,
        },
      });
    } else {
      setting = await prisma.webinarSetting.create({
        data: {
          youtubeVideoId: videoId,
          webinarTitle: webinar_title || 'Webinar',
          webinarDescription: webinar_description || '',
          webinarDate: webinar_date || '',
          webinarTime: webinar_time || '',
          webinarSpeaker: webinar_speaker || '',
          startTime: start_time ? new Date(start_time) : null,
          endTime: end_time ? new Date(end_time) : null,
          noWebinar: no_webinar ?? false,
        },
      });
    }

    // Update Redis cache
    const cacheData = {
      embed_url: buildEmbedUrl(setting.youtubeVideoId),
      youtube_video_id: setting.youtubeVideoId,
      webinar_title: setting.webinarTitle,
      webinar_description: setting.webinarDescription,
      webinar_date: setting.webinarDate,
      webinar_time: setting.webinarTime,
      webinar_speaker: setting.webinarSpeaker,
      start_time: setting.startTime?.toISOString() ?? null,
      end_time: setting.endTime?.toISOString() ?? null,
      no_webinar: setting.noWebinar,
    };

    await redis.set(KEYS.webinarSettings, JSON.stringify(cacheData));

    // Emit event for real-time updates
    wsEvents.emit('settings_updated', { type: 'its' });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Update webinar settings error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to update settings' },
      { status: 500 }
    );
  }
}
