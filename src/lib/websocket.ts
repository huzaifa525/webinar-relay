// WebSocket event emitter for real-time updates
// This is a simple in-memory event system for Next.js
// For production, use Redis Pub/Sub or a service like Pusher

type WebSocketEvent =
  | 'user_connected'
  | 'user_disconnected'
  | 'session_created'
  | 'session_deleted'
  | 'ids_updated'
  | 'settings_updated';

type EventCallback = (data: any) => void;

class EventEmitter {
  private listeners: Map<WebSocketEvent, Set<EventCallback>> = new Map();

  on(event: WebSocketEvent, callback: EventCallback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: WebSocketEvent, callback: EventCallback) {
    this.listeners.get(event)?.delete(callback);
  }

  emit(event: WebSocketEvent, data?: any) {
    this.listeners.get(event)?.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Event listener error:', error);
      }
    });
  }
}

export const wsEvents = new EventEmitter();
