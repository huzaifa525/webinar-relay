'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';

export default function RoleSelection() {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [error, setError] = useState('');
  const router = useRouter();
  const searchParams = useSearchParams();
  const userId = searchParams.get('user_id') || '';

  const handleSelectRole = async (role: 'its' | 'majlis') => {
    setIsLoading(role);
    setError('');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, selected_role: role }),
      });

      const data = await res.json();

      if (data.success) {
        router.push(data.redirect);
      } else {
        setError(data.error || 'Failed to login. Please try again.');
      }
    } catch {
      setError('Connection error. Please try again.');
    } finally {
      setIsLoading(null);
    }
  };

  return (
    <div className="role-page">
      <div className="role-container">
        {/* Logo */}
        <div className="role-logo-section">
          <div className="role-logo-ring">
            <Image
              src="https://i.ibb.co/nqfBrMmC/logo-without-back.png"
              alt="Logo"
              width={64}
              height={64}
              className="rounded-full"
              priority
            />
          </div>
        </div>

        {/* Card */}
        <div className="role-card">
          <div className="role-header">
            <h2>Select Portal</h2>
            <p>Your ID is registered in both systems</p>
          </div>

          {/* User Badge */}
          <div className="role-badge-wrap">
            <span className="role-badge">
              <i className="fas fa-user" />
              ID: <strong>{userId}</strong>
            </span>
          </div>

          {error && (
            <div className="role-error">
              <i className="fas fa-exclamation-circle" />
              <span>{error}</span>
            </div>
          )}

          {/* Portal Options */}
          <div className="role-grid">
            <button
              onClick={() => handleSelectRole('its')}
              disabled={isLoading !== null}
              className="role-option"
            >
              <div className="role-option-icon">
                <i className="fas fa-book-open" />
              </div>
              <h3>Asbaaq Portal</h3>
              <p>Access Asbaaq webinar stream</p>
              {isLoading === 'its' && (
                <i className="fas fa-spinner fa-spin role-spinner" />
              )}
            </button>

            <button
              onClick={() => handleSelectRole('majlis')}
              disabled={isLoading !== null}
              className="role-option"
            >
              <div className="role-option-icon role-option-icon--alt">
                <i className="fas fa-mosque" />
              </div>
              <h3>Majlis Portal</h3>
              <p>Access Majlis webinar stream</p>
              {isLoading === 'majlis' && (
                <i className="fas fa-spinner fa-spin role-spinner" />
              )}
            </button>
          </div>

          <div className="role-back">
            <a href="/">
              <i className="fas fa-arrow-left" />
              Back to Login
            </a>
          </div>
        </div>
      </div>

      <style jsx>{`
        .role-page {
          min-height: 100dvh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px 16px;
          background:
            radial-gradient(ellipse at 50% 0%, rgba(10, 61, 160, 0.12) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 50%, rgba(212, 175, 55, 0.06) 0%, transparent 50%),
            linear-gradient(180deg, #090d1b 0%, #0a0f22 50%, #090d1b 100%);
        }
        .role-container {
          width: 100%;
          max-width: 460px;
          animation: slideUp 0.6s ease;
        }

        .role-logo-section {
          text-align: center;
          margin-bottom: 20px;
        }
        .role-logo-ring {
          width: 72px;
          height: 72px;
          margin: 0 auto;
          border-radius: 50%;
          padding: 4px;
          background: linear-gradient(135deg, rgba(212, 175, 55, 0.4), rgba(28, 84, 197, 0.3));
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .role-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.07);
          border-radius: 16px;
          padding: 28px 24px;
          backdrop-filter: blur(12px);
        }
        .role-header {
          text-align: center;
          margin-bottom: 16px;
        }
        .role-header h2 {
          font-family: 'Montserrat', sans-serif;
          font-size: 20px;
          font-weight: 700;
          background: linear-gradient(135deg, #d4af37, #f0cc50);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin-bottom: 4px;
        }
        .role-header p {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.45);
        }

        .role-badge-wrap {
          display: flex;
          justify-content: center;
          margin-bottom: 20px;
        }
        .role-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 14px;
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 100px;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.6);
        }
        .role-badge i {
          color: #d4af37;
          font-size: 12px;
        }
        .role-badge strong {
          color: #d4af37;
          font-weight: 600;
        }

        .role-error {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 10px 16px;
          margin-bottom: 18px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.2);
          border-radius: 10px;
          color: #ef4444;
          font-size: 13px;
        }

        .role-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        .role-option {
          padding: 24px 16px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 14px;
          cursor: pointer;
          text-align: center;
          transition: all 0.25s ease;
          color: #fff;
        }
        .role-option:hover:not(:disabled) {
          background: rgba(212, 175, 55, 0.05);
          border-color: rgba(212, 175, 55, 0.3);
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }
        .role-option:active:not(:disabled) {
          transform: translateY(0);
        }
        .role-option:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .role-option-icon {
          width: 48px;
          height: 48px;
          margin: 0 auto 12px;
          border-radius: 12px;
          background: rgba(212, 175, 55, 0.1);
          border: 1px solid rgba(212, 175, 55, 0.15);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          color: #d4af37;
          transition: all 0.25s ease;
        }
        .role-option:hover .role-option-icon {
          background: rgba(212, 175, 55, 0.15);
          border-color: rgba(212, 175, 55, 0.3);
        }
        .role-option-icon--alt {
          background: rgba(28, 84, 197, 0.1);
          border-color: rgba(28, 84, 197, 0.15);
          color: #5b8def;
        }
        .role-option:hover .role-option-icon--alt {
          background: rgba(28, 84, 197, 0.15);
          border-color: rgba(28, 84, 197, 0.3);
        }

        .role-option h3 {
          font-size: 15px;
          font-weight: 600;
          color: #d4af37;
          margin-bottom: 4px;
        }
        .role-option:nth-child(2) h3 {
          color: #5b8def;
        }
        .role-option p {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.4);
          line-height: 1.4;
        }

        .role-spinner {
          display: block;
          margin-top: 10px;
          color: #d4af37;
        }

        .role-back {
          text-align: center;
          margin-top: 20px;
        }
        .role-back a {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.35);
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          transition: color 0.2s ease;
        }
        .role-back a:hover {
          color: rgba(255, 255, 255, 0.6);
        }

        @media (max-width: 640px) {
          .role-page { padding: 20px 14px; }
          .role-container { max-width: 100%; }
          .role-card { padding: 22px 18px; border-radius: 14px; }
          .role-header h2 { font-size: 18px; }
          .role-header p { font-size: 12px; }
          .role-logo-ring { width: 64px; height: 64px; }
          .role-option { padding: 20px 14px; min-height: 48px; }
          .role-option h3 { font-size: 14px; }
          .role-option p { font-size: 11px; }
          .role-option-icon { width: 44px; height: 44px; font-size: 16px; }
        }

        @media (max-width: 480px) {
          .role-grid {
            grid-template-columns: 1fr;
          }
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @media (prefers-reduced-motion: reduce) {
          .role-container { animation: none; }
        }
      `}</style>
    </div>
  );
}
