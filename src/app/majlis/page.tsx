import { requireSession } from '@/lib/auth';
import { loadWebinarSettingsWithTimeCheck } from '@/lib/cache';
import YouTubePlayer from '@/components/YouTubePlayer';
import NoWebinar from '@/components/NoWebinar';

export const dynamic = 'force-dynamic';

export default async function MajlisPage() {
  const { session } = await requireSession('majlis');
  const settings = await loadWebinarSettingsWithTimeCheck('majlis');

  if (settings.no_webinar) {
    return <NoWebinar userId={session.user_id} userType="majlis" />;
  }

  return (
    <YouTubePlayer
      settings={settings}
      userId={session.user_id}
      userType="majlis"
    />
  );
}
