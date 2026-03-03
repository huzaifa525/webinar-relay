'use client';

import { useEffect } from 'react';
import Image from 'next/image';
import SessionDropdown from './SessionDropdown';
import type { UserType } from '@/types';

interface NoWebinarProps {
  userId: string;
  userType: UserType;
}

export default function NoWebinar({ userId, userType }: NoWebinarProps) {
  // Poll for webinar updates every 30 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const type = userType === 'its' ? 'webinar-settings' : 'majlis-settings';
        const res = await fetch(`/api/admin/${type}`);
        const data = await res.json();
        if (data && !data.no_webinar) {
          window.location.reload();
        }
      } catch {
        // Ignore errors
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [userType]);

  return (
    <div className="nw-page">
      {/* Header */}
      <header className="nw-header">
        <div className="nw-header-left">
          <Image
            src="https://i.ibb.co/nqfBrMmC/logo-without-back.png"
            alt="Logo"
            width={38}
            height={38}
            className="rounded-full"
          />
          <div>
            <h1 className="nw-brand">Anjuman e Hakimi</h1>
            <p className="nw-brand-sub">Live Relay Portal</p>
          </div>
        </div>
        <SessionDropdown userId={userId} userType={userType} />
      </header>

      {/* Content */}
      <div className="nw-content">
        <div className="nw-card">
          <div className="nw-icon-wrap">
            <i className="fas fa-satellite-dish" />
          </div>

          <h2 className="nw-title">No Stream Available</h2>

          <span className="nw-badge">
            <span className="nw-badge-dot" />
            Offline
          </span>

          <p className="nw-desc">
            There is currently no active webinar stream. The page will
            automatically refresh when a stream becomes available.
          </p>

          <div className="nw-checking">
            <div className="nw-checking-dot" />
            Checking for updates…
          </div>
        </div>
      </div>

      <style jsx>{`
        .nw-page {
          min-height: 100vh;
          background:
            radial-gradient(ellipse at 50% 0%, rgba(10, 61, 160, 0.10) 0%, transparent 50%),
            linear-gradient(180deg, #090d1b 0%, #0a0f22 50%, #090d1b 100%);
        }

        .nw-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 20px;
          background: rgba(15, 20, 40, 0.6);
          backdrop-filter: blur(12px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .nw-header-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .nw-brand {
          font-family: 'Montserrat', sans-serif;
          font-size: 14px;
          font-weight: 700;
          background: linear-gradient(135deg, #d4af37, #f0cc50);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          line-height: 1.2;
        }
        .nw-brand-sub {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.35);
          line-height: 1.2;
        }

        .nw-content {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: calc(100dvh - 64px);
          padding: 24px 16px;
        }

        .nw-card {
          text-align: center;
          max-width: 360px;
          animation: slideUp 0.6s ease;
        }

        .nw-icon-wrap {
          width: 80px;
          height: 80px;
          margin: 0 auto 20px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.07);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 28px;
          color: rgba(212, 175, 55, 0.4);
        }

        .nw-title {
          font-family: 'Montserrat', sans-serif;
          font-size: 22px;
          font-weight: 700;
          background: linear-gradient(135deg, #d4af37, #f0cc50);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin-bottom: 12px;
        }

        .nw-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 14px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.2);
          border-radius: 100px;
          font-size: 12px;
          font-weight: 600;
          color: #ef4444;
          margin-bottom: 16px;
        }
        .nw-badge-dot {
          width: 6px;
          height: 6px;
          background: #ef4444;
          border-radius: 50%;
        }

        .nw-desc {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.45);
          line-height: 1.6;
        }

        .nw-checking {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-top: 28px;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.25);
        }
        .nw-checking-dot {
          width: 6px;
          height: 6px;
          background: rgba(212, 175, 55, 0.4);
          border-radius: 50%;
          animation: pulse 1.5s ease-in-out infinite;
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }

        @media (prefers-reduced-motion: reduce) {
          .nw-card { animation: none; }
          .nw-checking-dot { animation: none; opacity: 0.6; }
        }

        /* MOBILE */
        @media (max-width: 640px) {
          .nw-header { padding: 10px 14px; }
          .nw-brand { font-size: 13px; }
          .nw-brand-sub { font-size: 10px; }
          .nw-content { padding: 20px 14px; min-height: calc(100vh - 56px); min-height: calc(100dvh - 56px); }
          .nw-card { max-width: 300px; }
          .nw-icon-wrap { width: 68px; height: 68px; font-size: 24px; margin-bottom: 16px; }
          .nw-title { font-size: 20px; }
          .nw-desc { font-size: 12px; }
          .nw-badge { font-size: 11px; padding: 4px 12px; }
        }
      `}</style>
    </div>
  );
}
