'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface SessionDropdownProps {
  userId: string;
  userType: 'its' | 'majlis';
}

export default function SessionDropdown({ userId, userType }: SessionDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/');
  };

  const handleForceLogout = async () => {
    if (!confirm('This will log out ALL your devices. Continue?')) return;
    await fetch('/api/auth/force-logout', { method: 'POST' });
    router.push('/');
  };

  const label = userType === 'its' ? 'Asbaaq' : 'Majlis';

  return (
    <div ref={dropdownRef} style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="sd-trigger"
      >
        <i className="fas fa-user sd-trigger-icon" />
        <span className="sd-trigger-text">
          {label}: <strong>{userId}</strong>
        </span>
        <i className={`fas fa-chevron-down sd-chevron ${isOpen ? 'sd-chevron--open' : ''}`} />
      </button>

      {isOpen && (
        <div className="sd-menu">
          <div className="sd-menu-header">
            <p className="sd-menu-label">Logged in as</p>
            <p className="sd-menu-value">{label} ID: {userId}</p>
          </div>

          <button onClick={handleLogout} className="sd-menu-item">
            <i className="fas fa-sign-out-alt" />
            Logout this device
          </button>

          <button onClick={handleForceLogout} className="sd-menu-item sd-menu-item--danger">
            <i className="fas fa-power-off" />
            Logout all devices
          </button>
        </div>
      )}

      <style jsx>{`
        .sd-trigger {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 7px 14px;
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 100px;
          cursor: pointer;
          color: #fff;
          transition: all 0.2s ease;
        }
        .sd-trigger:hover {
          border-color: rgba(212, 175, 55, 0.3);
          background: rgba(255, 255, 255, 0.06);
        }
        .sd-trigger-icon {
          font-size: 12px;
          color: #d4af37;
        }
        .sd-trigger-text {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.7);
        }
        .sd-trigger-text strong {
          color: #d4af37;
          font-weight: 600;
        }
        .sd-chevron {
          font-size: 10px;
          color: rgba(255, 255, 255, 0.35);
          transition: transform 0.2s ease;
        }
        .sd-chevron--open {
          transform: rotate(180deg);
        }

        .sd-menu {
          position: absolute;
          right: 0;
          top: calc(100% + 8px);
          width: 220px;
          background: rgba(15, 20, 40, 0.95);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          backdrop-filter: blur(16px);
          box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
          overflow: hidden;
          z-index: 50;
          animation: menuIn 0.2s ease;
        }

        .sd-menu-header {
          padding: 12px 16px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .sd-menu-label {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.4);
          margin-bottom: 2px;
        }
        .sd-menu-value {
          font-size: 13px;
          color: #d4af37;
          font-weight: 600;
        }

        .sd-menu-item {
          width: 100%;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 11px 16px;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.7);
          transition: background 0.15s ease;
          text-align: left;
        }
        .sd-menu-item:hover {
          background: rgba(255, 255, 255, 0.05);
        }
        .sd-menu-item i {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.4);
          width: 16px;
          text-align: center;
        }

        .sd-menu-item--danger {
          color: #ef4444;
          border-top: 1px solid rgba(255, 255, 255, 0.06);
        }
        .sd-menu-item--danger:hover {
          background: rgba(239, 68, 68, 0.08);
        }
        .sd-menu-item--danger i {
          color: rgba(239, 68, 68, 0.6);
        }

        @keyframes menuIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* MOBILE */
        @media (max-width: 640px) {
          .sd-trigger { padding: 6px 10px; gap: 6px; }
          .sd-trigger-text { font-size: 12px; }
          .sd-trigger-icon { font-size: 11px; }
          .sd-chevron { font-size: 9px; }
          .sd-menu { width: 200px; }
          .sd-menu-header { padding: 10px 14px; }
          .sd-menu-item { padding: 12px 14px; font-size: 13px; min-height: 44px; }
        }

        @media (max-width: 380px) {
          .sd-trigger-text { display: none; }
          .sd-trigger { padding: 8px 10px; }
        }
      `}</style>
    </div>
  );
}
