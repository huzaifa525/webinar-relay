import { NextRequest } from 'next/server';
import { redis } from '@/lib/redis';
import { wsEvents } from '@/lib/websocket';

async function verifyAdmin(request: NextRequest): Promise<boolean> {
  const adminToken = request.cookies.get('admin_session')?.value;
  if (!adminToken) return false;
  const data = await redis.get(`admin_sessions:${adminToken}`);
  return !!data;
}

export async function GET(request: NextRequest) {
  if (!(await verifyAdmin(request))) {
    return new Response('Unauthorized', { status: 401 });
  }

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      // Send initial connection message
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'connected' })}\n\n`));

      // Listen to all events
      const handleUserConnected = (data: any) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'user_connected', data })}\n\n`));
      };

      const handleUserDisconnected = (data: any) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'user_disconnected', data })}\n\n`));
      };

      const handleIdsUpdated = (data: any) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'ids_updated', data })}\n\n`));
      };

      const handleSettingsUpdated = (data: any) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'settings_updated', data })}\n\n`));
      };

      wsEvents.on('user_connected', handleUserConnected);
      wsEvents.on('user_disconnected', handleUserDisconnected);
      wsEvents.on('ids_updated', handleIdsUpdated);
      wsEvents.on('settings_updated', handleSettingsUpdated);

      // Cleanup on close
      request.signal.addEventListener('abort', () => {
        wsEvents.off('user_connected', handleUserConnected);
        wsEvents.off('user_disconnected', handleUserDisconnected);
        wsEvents.off('ids_updated', handleIdsUpdated);
        wsEvents.off('settings_updated', handleSettingsUpdated);
        controller.close();
      });

      // Keep-alive ping every 30 seconds
      const keepAlive = setInterval(() => {
        controller.enqueue(encoder.encode(`: keepalive\n\n`));
      }, 30000);

      request.signal.addEventListener('abort', () => {
        clearInterval(keepAlive);
      });
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
