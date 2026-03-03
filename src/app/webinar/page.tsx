import { requireSession } from '@/lib/auth';
import { loadWebinarSettingsWithTimeCheck } from '@/lib/cache';
import YouTubePlayer from '@/components/YouTubePlayer';
import NoWebinar from '@/components/NoWebinar';

export const dynamic = 'force-dynamic';

export default async function WebinarPage() {
  const { session } = await requireSession('its');
  const settings = await loadWebinarSettingsWithTimeCheck('its');

  if (settings.no_webinar) {
    return <NoWebinar userId={session.user_id} userType="its" />;
  }

  return (
    <YouTubePlayer
      settings={settings}
      userId={session.user_id}
      userType="its"
    />
  );
}
