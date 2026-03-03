'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

export default function LoginForm() {
  const [userId, setUserId] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Disable developer tools
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F12') e.preventDefault();
      if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J')) e.preventDefault();
      if (e.ctrlKey && e.key === 'u') e.preventDefault();
    };
    const handleContextMenu = (e: MouseEvent) => e.preventDefault();

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('contextmenu', handleContextMenu);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('contextmenu', handleContextMenu);
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const digits = e.target.value.replace(/\D/g, '').slice(0, 8);
    setUserId(digits);
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (userId.length !== 8) {
      setError('Please enter a valid 8-digit ID');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });

      const data = await res.json();

      if (data.success) {
        if (data.redirect === '/select-role') {
          router.push(`/select-role?user_id=${userId}`);
        } else {
          router.push(data.redirect);
        }
      } else {
        setError(data.error || 'Access denied. Your ID is not authorized.');
      }
    } catch {
      setError('Connection error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const filled = userId.length;

  return (
    <div className="login-page">
      <div className="login-container">
        {/* Logo & Branding */}
        <div className="login-logo-section">
          <div className="login-logo-ring">
            <Image
              src="https://i.ibb.co/nqfBrMmC/logo-without-back.png"
              alt="Logo"
              width={80}
              height={80}
              className="rounded-full"
              priority
            />
          </div>
          <h1 className="login-title">Anjuman e Hakimi</h1>
          <p className="login-subtitle">Najmi Mohallah Ratlam</p>
        </div>

        {/* Login Card */}
        <div className="login-card">
          <div className="login-card-header">
            <h2>Welcome Back</h2>
            <p>Enter your 8-digit ID to access the live stream</p>
          </div>

          {error && (
            <div className="login-error">
              <i className="fas fa-exclamation-circle" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="login-field">
              <label htmlFor="user-id">Asbaaq / Majlis ID</label>
              <div className="login-input-wrap">
                <i aria-hidden="true" className="fas fa-id-card login-input-icon" />
                <input
                  id="user-id"
                  ref={inputRef}
                  type="text"
                  inputMode="numeric"
                  pattern="\d{8}"
                  maxLength={8}
                  value={userId}
                  onChange={handleInputChange}
                  placeholder="Enter 8-digit ID"
                  className="login-input"
                  required
                  autoComplete="off"
                  spellCheck={false}
                />
              </div>

              {/* Digit progress dots */}
              <div className="login-dots">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div
                    key={i}
                    className={`login-dot ${i < filled ? 'login-dot--filled' : ''}`}
                  />
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || filled !== 8}
              className="login-submit"
            >
              {isLoading ? (
                <>
                  <i className="fas fa-spinner fa-spin" />
                  Verifying...
                </>
              ) : (
                <>
                  <i className="fas fa-broadcast-tower" />
                  Access Live Stream
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer Links */}
        <div className="login-footer">
          <a href="/admin/login" className="login-admin-link">
            <i className="fas fa-lock" />
            Admin Panel
          </a>
        </div>

        <p className="login-credit">
          Developed with <span className="login-heart">&#10084;</span> by Huzefa Nalkheda wala
        </p>
      </div>

      <style jsx>{`
        .login-page {
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

        .login-container {
          width: 100%;
          max-width: 400px;
          animation: slideUp 0.6s ease;
        }

        /* Logo */
        .login-logo-section {
          text-align: center;
          margin-bottom: 28px;
        }
        .login-logo-ring {
          width: 88px;
          height: 88px;
          margin: 0 auto 14px;
          border-radius: 50%;
          padding: 4px;
          background: linear-gradient(135deg, rgba(212, 175, 55, 0.4), rgba(28, 84, 197, 0.3));
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .login-title {
          font-family: 'Montserrat', sans-serif;
          font-size: 22px;
          font-weight: 700;
          background: linear-gradient(135deg, #d4af37, #f0cc50);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .login-subtitle {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.4);
          margin-top: 2px;
        }

        /* Card */
        .login-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.07);
          border-radius: 16px;
          padding: 28px 24px;
          backdrop-filter: blur(12px);
        }
        .login-card-header {
          text-align: center;
          margin-bottom: 24px;
        }
        .login-card-header h2 {
          font-size: 18px;
          font-weight: 600;
          color: #fff;
          margin-bottom: 4px;
        }
        .login-card-header p {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.45);
        }

        /* Error */
        .login-error {
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
          animation: shake 0.4s ease;
        }

        /* Field */
        .login-field {
          margin-bottom: 20px;
        }
        .login-field label {
          display: block;
          font-size: 12px;
          font-weight: 500;
          color: rgba(255, 255, 255, 0.5);
          margin-bottom: 8px;
        }
        .login-input-wrap {
          position: relative;
        }
        .login-input-icon {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: rgba(212, 175, 55, 0.5);
          font-size: 14px;
        }
        .login-input {
          width: 100%;
          padding: 14px 16px 14px 44px;
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          color: #fff;
          font-size: 18px;
          font-family: 'Courier New', monospace;
          letter-spacing: 4px;
          outline: none;
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .login-input::placeholder {
          font-size: 14px;
          letter-spacing: 0;
          font-family: 'Inter', sans-serif;
          color: rgba(255, 255, 255, 0.2);
        }
        .login-input:focus {
          border-color: rgba(212, 175, 55, 0.4);
          box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.08);
        }

        /* Digit dots */
        .login-dots {
          display: flex;
          justify-content: center;
          gap: 6px;
          margin-top: 12px;
        }
        .login-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.08);
          transition: all 0.2s ease;
        }
        .login-dot--filled {
          background: #d4af37;
          box-shadow: 0 0 8px rgba(212, 175, 55, 0.3);
        }

        /* Submit */
        .login-submit {
          width: 100%;
          padding: 14px 20px;
          background: linear-gradient(135deg, #d4af37, #b39128);
          border: none;
          border-radius: 12px;
          color: #fff;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          transition: all 0.2s ease;
        }
        .login-submit:hover:not(:disabled) {
          background: linear-gradient(135deg, #e0be48, #c49e30);
          transform: translateY(-1px);
          box-shadow: 0 8px 24px rgba(212, 175, 55, 0.25);
        }
        .login-submit:active:not(:disabled) {
          transform: translateY(0);
        }
        .login-submit:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        /* Footer */
        .login-footer {
          text-align: center;
          margin-top: 24px;
        }
        .login-admin-link {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.25);
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          transition: color 0.2s ease;
        }
        .login-admin-link:hover {
          color: rgba(255, 255, 255, 0.5);
        }
        .login-credit {
          text-align: center;
          margin-top: 14px;
          font-size: 11px;
          color: rgba(255, 255, 255, 0.15);
        }
        .login-heart {
          color: #ef4444;
          display: inline-block;
          animation: heartbeat 1.2s ease-in-out infinite;
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-6px); }
          75% { transform: translateX(6px); }
        }
        @keyframes heartbeat {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.2); }
        }

        /* TABLET */
        @media (max-width: 768px) {
          .login-page { padding: 20px 16px; }
        }

        /* MOBILE */
        @media (max-width: 480px) {
          .login-page { padding: 16px 12px; }
          .login-container { max-width: 100%; }
          .login-logo-ring { width: 76px; height: 76px; }
          .login-title { font-size: 20px; }
          .login-subtitle { font-size: 12px; }
          .login-card { padding: 22px 18px; border-radius: 14px; }
          .login-card-header h2 { font-size: 16px; }
          .login-card-header p { font-size: 12px; }
          .login-input { font-size: 16px; padding: 14px 14px 14px 42px; }
          .login-submit { padding: 14px 18px; font-size: 15px; min-height: 48px; }
          .login-dot { width: 7px; height: 7px; }
          .login-dots { gap: 5px; }
        }

        @media (prefers-reduced-motion: reduce) {
          .login-container { animation: none; }
          .login-error { animation: none; }
          .login-heart { animation: none; }
        }

        /* SMALL MOBILE */
        @media (max-width: 360px) {
          .login-logo-ring { width: 68px; height: 68px; }
          .login-title { font-size: 18px; }
          .login-card { padding: 20px 14px; }
          .login-input { letter-spacing: 3px; }
        }
      `}</style>
    </div>
  );
}
