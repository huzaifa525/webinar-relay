import { NextRequest } from 'next/server';
import { verifySession } from '@/lib/session';
import { wsEvents } from '@/lib/websocket';

export async function GET(request: NextRequest) {
  const token = request.cookies.get('session_token')?.value;

  if (!token) {
    return new Response('Unauthorized', { status: 401 });
  }

  const session = await verifySession(token);
  if (!session) {
    return new Response('Unauthorized', { status: 401 });
  }

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      // Send initial connection message
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'connected' })}\n\n`));

      // Listen for force logout for this specific user
      const handleUserDisconnected = (data: any) => {
        if (data.user_id === session.user_id && data.user_type === session.user_type) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'force_logout' })}\n\n`));
        }
      };

      wsEvents.on('user_disconnected', handleUserDisconnected);

      // Cleanup on close
      request.signal.addEventListener('abort', () => {
        wsEvents.off('user_disconnected', handleUserDisconnected);
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
