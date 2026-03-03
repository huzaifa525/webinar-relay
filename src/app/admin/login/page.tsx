'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function AdminLoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (data.success) {
        router.push('/admin/dashboard');
      } else {
        setError(data.error || 'Invalid credentials');
      }
    } catch {
      setError('Connection error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="adm-login-page">
      <div className="adm-login-container">
        <div className="adm-login-card">
          {/* Icon */}
          <div className="adm-login-icon-wrap">
            <div className="adm-login-icon">
              <i className="fas fa-shield-alt" />
            </div>
            <h2 className="adm-login-title">Admin Panel</h2>
            <p className="adm-login-sub">Authorized access only</p>
          </div>

          {error && (
            <div className="adm-login-error">
              <i className="fas fa-exclamation-circle" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="adm-login-field">
              <label>Username</label>
              <div className="adm-login-input-wrap">
                <i className="fas fa-user" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                  required
                  autoComplete="username"
                />
              </div>
            </div>

            <div className="adm-login-field">
              <label>Password</label>
              <div className="adm-login-input-wrap">
                <i className="fas fa-key" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="adm-login-submit"
            >
              {isLoading ? (
                <>
                  <i className="fas fa-spinner fa-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  <i className="fas fa-lock" />
                  Login
                </>
              )}
            </button>
          </form>

          <div className="adm-login-back">
            <a href="/">
              <i className="fas fa-arrow-left" />
              Back to User Login
            </a>
          </div>
        </div>
      </div>

      <style jsx>{`
        .adm-login-page {
          min-height: 100dvh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px 16px;
          background:
            radial-gradient(ellipse at 50% 0%, rgba(10, 61, 160, 0.12) 0%, transparent 50%),
            linear-gradient(180deg, #090d1b 0%, #0a0f22 50%, #090d1b 100%);
        }
        .adm-login-container {
          width: 100%;
          max-width: 400px;
          animation: slideUp 0.6s ease;
        }

        .adm-login-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.07);
          border-radius: 16px;
          padding: 32px 24px;
          backdrop-filter: blur(12px);
        }

        .adm-login-icon-wrap {
          text-align: center;
          margin-bottom: 24px;
        }
        .adm-login-icon {
          width: 56px;
          height: 56px;
          margin: 0 auto 12px;
          border-radius: 14px;
          background: rgba(10, 61, 160, 0.15);
          border: 1px solid rgba(10, 61, 160, 0.25);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 22px;
          color: #d4af37;
        }
        .adm-login-title {
          font-family: 'Montserrat', sans-serif;
          font-size: 20px;
          font-weight: 700;
          background: linear-gradient(135deg, #d4af37, #f0cc50);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .adm-login-sub {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.35);
          margin-top: 2px;
        }

        .adm-login-error {
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

        .adm-login-field {
          margin-bottom: 16px;
        }
        .adm-login-field label {
          display: block;
          font-size: 12px;
          font-weight: 500;
          color: rgba(255, 255, 255, 0.5);
          margin-bottom: 6px;
        }
        .adm-login-input-wrap {
          position: relative;
        }
        .adm-login-input-wrap i {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: rgba(255, 255, 255, 0.25);
          font-size: 13px;
        }
        .adm-login-input-wrap input {
          width: 100%;
          padding: 12px 16px 12px 40px;
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 10px;
          color: #fff;
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .adm-login-input-wrap input::placeholder {
          color: rgba(255, 255, 255, 0.2);
        }
        .adm-login-input-wrap input:focus {
          border-color: rgba(212, 175, 55, 0.4);
          box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.08);
        }

        .adm-login-submit {
          width: 100%;
          padding: 13px 20px;
          margin-top: 8px;
          background: linear-gradient(135deg, #d4af37, #b39128);
          border: none;
          border-radius: 12px;
          color: #fff;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          transition: all 0.2s ease;
        }
        .adm-login-submit:hover:not(:disabled) {
          background: linear-gradient(135deg, #e0be48, #c49e30);
          transform: translateY(-1px);
          box-shadow: 0 8px 24px rgba(212, 175, 55, 0.25);
        }
        .adm-login-submit:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .adm-login-back {
          text-align: center;
          margin-top: 20px;
        }
        .adm-login-back a {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.3);
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          transition: color 0.2s ease;
        }
        .adm-login-back a:hover {
          color: rgba(255, 255, 255, 0.55);
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

        @media (prefers-reduced-motion: reduce) {
          .adm-login-container { animation: none; }
          .adm-login-error { animation: none; }
        }

        /* MOBILE */
        @media (max-width: 480px) {
          .adm-login-page { padding: 16px 12px; }
          .adm-login-container { max-width: 100%; }
          .adm-login-card { padding: 24px 18px; border-radius: 14px; }
          .adm-login-icon { width: 50px; height: 50px; font-size: 20px; }
          .adm-login-title { font-size: 18px; }
          .adm-login-input-wrap input { font-size: 16px; padding: 13px 14px 13px 38px; }
          .adm-login-submit { padding: 14px 18px; min-height: 48px; }
        }
      `}</style>
    </div>
  );
}
