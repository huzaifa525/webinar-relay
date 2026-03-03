'use client';

import { useState, useCallback } from 'react';
import type { Notification, NotificationType } from '@/types';

const ICONS: Record<NotificationType, string> = {
  success: 'fas fa-check-circle',
  error: 'fas fa-times-circle',
  warning: 'fas fa-exclamation-triangle',
  info: 'fas fa-info-circle',
};

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = useCallback(
    (type: NotificationType, message: string, duration: number = 5000) => {
      const id = Math.random().toString(36).substring(2, 9);
      setNotifications((prev) => [...prev, { id, type, message, duration }]);

      if (duration > 0) {
        setTimeout(() => {
          setNotifications((prev) => prev.filter((n) => n.id !== id));
        }, duration);
      }
    },
    []
  );

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  return { notifications, addNotification, removeNotification };
}

interface NotificationToastProps {
  notifications: Notification[];
  onRemove: (id: string) => void;
}

export default function NotificationToast({
  notifications,
  onRemove,
}: NotificationToastProps) {
  if (notifications.length === 0) return null;

  return (
    <div className="nt-container">
      {notifications.map((n) => (
        <div key={n.id} className={`nt-toast nt-toast--${n.type}`}>
          <i className={ICONS[n.type]} />
          <p className="nt-msg">{n.message}</p>
          <button onClick={() => onRemove(n.id)} className="nt-close">
            <i className="fas fa-times" />
          </button>
        </div>
      ))}

      <style jsx>{`
        .nt-container {
          position: fixed;
          top: 16px;
          right: 16px;
          z-index: 99999;
          display: flex;
          flex-direction: column;
          gap: 10px;
          max-width: 340px;
        }

        .nt-toast {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 12px 14px;
          border-radius: 10px;
          border: 1px solid;
          backdrop-filter: blur(12px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
          animation: ntSlideIn 0.3s ease;
          font-size: 13px;
        }

        .nt-toast--success {
          background: rgba(34, 197, 94, 0.12);
          border-color: rgba(34, 197, 94, 0.25);
          color: #22c55e;
        }
        .nt-toast--error {
          background: rgba(239, 68, 68, 0.12);
          border-color: rgba(239, 68, 68, 0.25);
          color: #ef4444;
        }
        .nt-toast--warning {
          background: rgba(249, 115, 22, 0.12);
          border-color: rgba(249, 115, 22, 0.25);
          color: #f97316;
        }
        .nt-toast--info {
          background: rgba(212, 175, 55, 0.12);
          border-color: rgba(212, 175, 55, 0.25);
          color: #d4af37;
        }

        .nt-toast i:first-child {
          margin-top: 1px;
          flex-shrink: 0;
        }

        .nt-msg {
          flex: 1;
          line-height: 1.4;
        }

        .nt-close {
          background: none;
          border: none;
          cursor: pointer;
          color: rgba(255, 255, 255, 0.4);
          padding: 0;
          font-size: 11px;
          transition: color 0.15s ease;
          flex-shrink: 0;
          margin-top: 1px;
        }
        .nt-close:hover {
          color: rgba(255, 255, 255, 0.7);
        }

        @keyframes ntSlideIn {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @media (max-width: 480px) {
          .nt-container {
            right: 10px;
            left: 10px;
            max-width: none;
          }
        }
      `}</style>
    </div>
  );
}
