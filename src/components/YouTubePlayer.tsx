'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Image from 'next/image';
import SessionDropdown from './SessionDropdown';
import NotificationToast, { useNotifications } from './NotificationToast';
import type { WebinarSettings, UserType } from '@/types';

interface YouTubePlayerProps {
  settings: WebinarSettings;
  userId: string;
  userType: UserType;
}

export default function YouTubePlayer({ settings, userId, userType }: YouTubePlayerProps) {
  const [isMuted, setIsMuted] = useState(true);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [isLoaded, setIsLoaded] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const hideTimerRef = useRef<NodeJS.Timeout | null>(null);


  const { notifications, addNotification, removeNotification } = useNotifications();

  const label = userType === 'its' ? 'Asbaaq' : 'Majlis';

  const resetHideTimer = useCallback(() => {
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    setShowControls(true);
    if (!isFullscreen) {
      hideTimerRef.current = setTimeout(() => setShowControls(false), 3000);
    }
  }, [isFullscreen]);

  const postYTCommand = useCallback((func: string) => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage(
        JSON.stringify({ event: 'command', func, args: '' }), '*'
      );
    }
  }, []);

  const toggleVolume = useCallback(() => {
    postYTCommand(isMuted ? 'unMute' : 'mute');
    setIsMuted(!isMuted);
  }, [isMuted, postYTCommand]);

  const togglePlayPause = useCallback(() => {
    postYTCommand(isPlaying ? 'pauseVideo' : 'playVideo');
    setIsPlaying(!isPlaying);
  }, [isPlaying, postYTCommand]);

  const toggleFullscreen = useCallback(async () => {
    if (!containerRef.current) return;
    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen();
        try { await (screen.orientation as any)?.lock?.('landscape'); } catch {}
      } else {
        await document.exitFullscreen();
      }
    } catch {}
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const h = () => resetHideTimer();
    el.addEventListener('mousemove', h);
    el.addEventListener('mouseenter', h);
    el.addEventListener('touchstart', h);
    el.addEventListener('click', h);
    resetHideTimer();
    return () => {
      el.removeEventListener('mousemove', h);
      el.removeEventListener('mouseenter', h);
      el.removeEventListener('touchstart', h);
      el.removeEventListener('click', h);
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    };
  }, [resetHideTimer]);

  useEffect(() => {
    const h = () => { setIsFullscreen(!!document.fullscreenElement); if (!document.fullscreenElement && screen.orientation?.unlock) screen.orientation.unlock(); };
    document.addEventListener('fullscreenchange', h);
    return () => document.removeEventListener('fullscreenchange', h);
  }, []);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      switch (e.key.toLowerCase()) {
        case ' ': case 'k': e.preventDefault(); togglePlayPause(); break;
        case 'm': toggleVolume(); break;
        case 'f': toggleFullscreen(); break;
      }
    };
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, [togglePlayPause, toggleVolume, toggleFullscreen]);

  useEffect(() => {
    let wl: WakeLockSentinel | null = null;
    async function acq() { try { if ('wakeLock' in navigator) wl = await navigator.wakeLock.request('screen'); } catch {} }
    acq();
    const v = () => { if (document.visibilityState === 'visible') acq(); };
    document.addEventListener('visibilitychange', v);
    return () => { document.removeEventListener('visibilitychange', v); wl?.release(); };
  }, []);

  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.key === 'F12') e.preventDefault(); if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J')) e.preventDefault(); if (e.ctrlKey && e.key === 'u') e.preventDefault(); };
    const c = (e: MouseEvent) => e.preventDefault();
    document.addEventListener('keydown', k); document.addEventListener('contextmenu', c);
    return () => { document.removeEventListener('keydown', k); document.removeEventListener('contextmenu', c); };
  }, []);

  useEffect(() => {
    addNotification('success', 'Connected to webinar stream');
    const sse = new EventSource('/api/auth/events');
    sse.onmessage = (ev) => { try { const { type } = JSON.parse(ev.data); if (type === 'force_logout') { addNotification('warning', 'Logged out by administrator'); setTimeout(async () => { await fetch('/api/auth/logout', { method: 'POST' }); window.location.href = '/'; }, 2000); } } catch {} };
    return () => { sse.close(); };
  }, [addNotification]);

  return (
    <>
      <NotificationToast notifications={notifications} onRemove={removeNotification} />

      <div className="page">
        {/* BG Glow */}
        <div className="bg-glow bg-glow-1" />
        <div className="bg-glow bg-glow-2" />

        {/* HEADER */}
        {!isFullscreen && (
          <header className="hdr">
            <div className="hdr-l">
              <div className="hdr-logo">
                <Image src="https://i.ibb.co/nqfBrMmC/logo-without-back.png" alt="Logo" width={36} height={36} className="rounded-full" />
              </div>
              <div>
                <div className="hdr-title">Anjuman e Hakimi</div>
                <div className="hdr-sub">Najmi Mohallah Ratlam</div>
              </div>
            </div>
            <SessionDropdown userId={userId} userType={userType} />
          </header>
        )}

        {/* BODY */}
        <div className={isFullscreen ? 'body-fs' : 'body'}>

          {/* INFO STRIP */}
          {!isFullscreen && (
            <div className="info">
              <div className="info-row">
                <div className="info-left">
                  <div className="live-pill"><span className="live-dot" />LIVE NOW</div>
                  <div className="info-type">{label} Stream</div>
                </div>
              </div>
              <h1 className="info-title">{settings.webinar_title}</h1>
            </div>
          )}

          {/* VIDEO */}
          <div ref={containerRef} className={`vid ${isFullscreen ? 'vid-fs' : ''}`}>
            <div className={isFullscreen ? 'vid-inner-fs' : 'vid-inner'}>
              <iframe ref={iframeRef} className={isFullscreen ? 'vid-frame-fs' : 'vid-frame'} src={settings.embed_url} allow="autoplay; encrypted-media; fullscreen" allowFullScreen title={settings.webinar_title} onLoad={() => setIsLoaded(true)} />
            </div>

            <div className="vid-click" onClick={togglePlayPause} />

            {!isPlaying && (
              <div className="play-wrap">
                <div className="play-btn"><i className="fas fa-play" /></div>
              </div>
            )}

            {/* CONTROLS */}
            <div className={`ctrl ${showControls || isFullscreen ? 'ctrl-on' : 'ctrl-off'}`}
              onMouseEnter={() => { if (hideTimerRef.current) clearTimeout(hideTimerRef.current); setShowControls(true); }}
              onMouseLeave={resetHideTimer}
            >
              <div className="ctrl-inner">
                <div className="ctrl-left">
                  <button onClick={e => { e.stopPropagation(); toggleVolume(); }} className="ctrl-btn" aria-label={isMuted ? 'Unmute' : 'Mute'} title={isMuted ? 'Unmute (M)' : 'Mute (M)'}>
                    <i aria-hidden="true" className={`fas ${isMuted ? 'fa-volume-mute' : 'fa-volume-up'}`} />
                  </button>
                  <span className="ctrl-live"><span className="ctrl-live-dot" />LIVE</span>
                  {isFullscreen && <span className="ctrl-title">{settings.webinar_title}</span>}
                </div>
                <div className="ctrl-right">
                  <button onClick={e => { e.stopPropagation(); toggleFullscreen(); }} className="ctrl-btn" aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'} title={isFullscreen ? 'Exit Fullscreen (F)' : 'Fullscreen (F)'}>
                    <i aria-hidden="true" className={`fas ${isFullscreen ? 'fa-compress' : 'fa-expand'}`} />
                  </button>
                </div>
              </div>
            </div>

            {!isLoaded && (
              <div className="loading">
                <div className="loading-ring" />
                <span className="loading-txt">Connecting to stream...</span>
              </div>
            )}
          </div>
        </div>

        {/* FOOTER */}
        {!isFullscreen && (
          <div className="ftr">
            Developed with <span className="ftr-h">&#10084;</span> by Huzefa Nalkheda wala
          </div>
        )}
      </div>

      <style jsx>{`
        .page {
          min-height: 100dvh;
          background: #0b0e1a;
          position: relative;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        /* Ambient glow blobs */
        .bg-glow {
          position: fixed;
          border-radius: 50%;
          filter: blur(120px);
          pointer-events: none;
          z-index: 0;
        }
        .bg-glow-1 {
          width: 500px; height: 500px;
          top: -150px; left: -100px;
          background: rgba(10, 61, 160, 0.18);
        }
        .bg-glow-2 {
          width: 400px; height: 400px;
          bottom: -100px; right: -80px;
          background: rgba(212, 175, 55, 0.08);
        }

        /* HEADER */
        .hdr {
          position: relative;
          z-index: 10;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 14px 24px;
          background: rgba(11, 14, 26, 0.7);
          backdrop-filter: blur(16px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .hdr-l { display: flex; align-items: center; gap: 12px; }
        .hdr-logo {
          width: 40px; height: 40px;
          border-radius: 10px;
          overflow: hidden;
          border: 1.5px solid rgba(212, 175, 55, 0.3);
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }
        .hdr-title {
          font-family: 'Montserrat', sans-serif;
          font-size: 16px;
          font-weight: 800;
          background: linear-gradient(to right, #e8d48b, #d4af37);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          line-height: 1.2;
        }
        .hdr-sub {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.35);
          font-weight: 400;
        }

        /* BODY */
        .body {
          flex: 1;
          position: relative;
          z-index: 1;
          max-width: 1060px;
          width: 100%;
          margin: 0 auto;
          padding: 24px 24px 32px;
        }
        .body-fs { flex: 1; position: relative; z-index: 1; }

        /* INFO */
        .info { margin-bottom: 20px; }
        .info-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .info-left { display: flex; align-items: center; gap: 10px; }
        .live-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 14px;
          background: linear-gradient(135deg, #dc2626, #b91c1c);
          border-radius: 20px;
          font-size: 11px;
          font-weight: 700;
          color: #fff;
          letter-spacing: 0.08em;
          box-shadow: 0 2px 12px rgba(220, 38, 38, 0.35);
        }
        .live-dot {
          width: 7px; height: 7px;
          background: #fff;
          border-radius: 50%;
          animation: pulse 1.5s ease-in-out infinite;
          box-shadow: 0 0 6px rgba(255, 255, 255, 0.5);
        }
        .info-type {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.4);
          font-weight: 500;
        }
        .info-title {
          font-family: 'Montserrat', sans-serif;
          font-size: 28px;
          font-weight: 800;
          color: #fff;
          line-height: 1.2;
          margin-bottom: 8px;
          letter-spacing: -0.02em;
        }
        /* VIDEO */
        .vid {
          position: relative;
          border-radius: 16px;
          overflow: hidden;
          background: #000;
          box-shadow:
            0 0 0 1px rgba(255, 255, 255, 0.06),
            0 20px 80px -10px rgba(0, 0, 0, 0.7),
            0 0 60px -20px rgba(10, 61, 160, 0.2);
        }
        .vid-fs {
          position: fixed;
          inset: 0;
          z-index: 9999;
          border-radius: 0;
          width: 100vw;
          height: 100vh;
          box-shadow: none;
        }
        .vid-inner { position: relative; padding-bottom: 56.25%; height: 0; }
        .vid-inner-fs { position: relative; height: 100vh; }
        .vid-frame {
          position: absolute;
          top: -50px; left: -50px;
          width: calc(100% + 100px);
          height: calc(100% + 100px);
          border: none;
        }
        .vid-frame-fs {
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 100%;
          border: none;
        }
        .vid-click { position: absolute; inset: 0; z-index: 10; cursor: pointer; }

        /* PLAY */
        .play-wrap {
          position: absolute; inset: 0;
          display: flex; align-items: center; justify-content: center;
          z-index: 11; pointer-events: none;
        }
        .play-btn {
          width: 72px; height: 72px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.12);
          backdrop-filter: blur(16px);
          border: 2px solid rgba(255, 255, 255, 0.2);
          display: flex; align-items: center; justify-content: center;
          animation: fadeScale 0.3s ease;
        }
        .play-btn i { font-size: 22px; color: #fff; margin-left: 4px; }

        /* CONTROLS */
        .ctrl {
          position: absolute; bottom: 0; left: 0; right: 0;
          z-index: 15;
          transition: opacity 0.3s, transform 0.3s;
        }
        .ctrl-on { opacity: 1; transform: translateY(0); }
        .ctrl-off { opacity: 0; transform: translateY(8px); pointer-events: none; }
        .ctrl-inner {
          display: flex; align-items: center; justify-content: space-between;
          padding: 14px 16px;
          background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.5) 60%, transparent 100%);
          pointer-events: auto;
        }
        .ctrl-left, .ctrl-right { display: flex; align-items: center; gap: 10px; }
        .ctrl-btn {
          width: 42px; height: 42px;
          display: flex; align-items: center; justify-content: center;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 50%;
          color: #fff;
          cursor: pointer;
          transition: all 0.2s;
          flex-shrink: 0;
        }
        .ctrl-btn:hover {
          background: rgba(255, 255, 255, 0.2);
          border-color: rgba(255, 255, 255, 0.3);
          transform: scale(1.08);
        }
        .ctrl-btn:active { transform: scale(0.92); }
        .ctrl-btn i { font-size: 15px; pointer-events: none; }
        .ctrl-live {
          display: flex; align-items: center; gap: 5px;
          font-size: 11px; font-weight: 700; color: #ef4444;
          letter-spacing: 0.05em;
        }
        .ctrl-live-dot {
          width: 6px; height: 6px;
          background: #ef4444; border-radius: 50%;
          animation: pulse 1.5s ease-in-out infinite;
        }
        .ctrl-title {
          font-size: 13px; color: rgba(255, 255, 255, 0.55);
          font-weight: 500;
          max-width: 260px;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }

        /* LOADING */
        .loading {
          position: absolute; inset: 0;
          background: #000;
          display: flex; flex-direction: column;
          align-items: center; justify-content: center;
          z-index: 20; gap: 16px;
        }
        .loading-ring {
          width: 44px; height: 44px;
          border: 3px solid rgba(255, 255, 255, 0.08);
          border-top-color: #d4af37;
          border-radius: 50%;
          animation: spin 0.9s linear infinite;
        }
        .loading-txt {
          font-size: 13px; color: rgba(255, 255, 255, 0.35);
          letter-spacing: 0.02em;
        }

        /* FOOTER */
        .ftr {
          text-align: center;
          padding: 20px 16px;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.3);
          position: relative;
          z-index: 1;
        }
        .ftr-h {
          color: #ef4444;
          display: inline-block;
          animation: heartbeat 1.3s ease-in-out infinite;
        }

        /* ANIMATIONS */
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.9); }
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes heartbeat {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.25); }
        }
        @keyframes fadeScale {
          from { opacity: 0; transform: scale(0.7); }
          to { opacity: 1; transform: scale(1); }
        }

        /* TABLET */
        @media (max-width: 1024px) {
          .body { max-width: 840px; padding: 20px 20px 28px; }
          .info-title { font-size: 24px; }
        }

        /* MOBILE */
        @media (max-width: 640px) {
          .hdr { padding: 10px 16px; }
          .hdr-title { font-size: 14px; }
          .hdr-sub { font-size: 10px; }
          .hdr-logo { width: 34px; height: 34px; border-radius: 8px; }
          .body { padding: 12px 12px 20px; }
          .info { margin-bottom: 14px; }
          .info-title { font-size: 18px; margin-bottom: 6px; }
          .info-type { font-size: 12px; }
          .live-pill { padding: 4px 10px; font-size: 10px; }
          .chip { padding: 4px 10px; font-size: 11px; }
          .chip i { font-size: 10px; }
          .vid { border-radius: 10px; }
          .ctrl-inner { padding: 10px 12px; }
          .ctrl-btn { width: 44px; height: 44px; }
          .ctrl-btn i { font-size: 14px; }
          .ctrl-live { font-size: 10px; }
          .ctrl-title { font-size: 12px; max-width: 140px; }
          .play-btn { width: 56px; height: 56px; }
          .play-btn i { font-size: 18px; }
          .ftr { padding: 16px 12px; font-size: 11px; }
          .bg-glow-1 { width: 300px; height: 300px; }
          .bg-glow-2 { width: 250px; height: 250px; }
        }

        /* SMALL MOBILE */
        @media (max-width: 380px) {
          .hdr { padding: 8px 12px; }
          .hdr-title { font-size: 13px; }
          .hdr-logo { width: 30px; height: 30px; }
          .body { padding: 10px 10px 16px; }
          .info-title { font-size: 16px; }
        }

        /* LANDSCAPE MOBILE */
        @media (max-width: 900px) and (orientation: landscape) {
          .hdr { display: none; }
          .body { padding: 0; max-width: none; }
          .info { display: none; }
          .vid { border-radius: 0; }
          .ftr { display: none; }
          .ctrl-btn { width: 40px; height: 40px; }
          .play-btn { width: 52px; height: 52px; }
        }

        /* Reduced motion */
        @media (prefers-reduced-motion: reduce) {
          .loading-ring { animation: none; border-top-color: #d4af37; }
          .live-dot, .ctrl-live-dot { animation: none; opacity: 1; }
          .ftr-h { animation: none; }
          .play-btn { animation: none; }
        }

        /* Notch safe areas for PWA */
        @supports (padding: env(safe-area-inset-top)) {
          .hdr {
            padding-left: max(16px, env(safe-area-inset-left));
            padding-right: max(16px, env(safe-area-inset-right));
          }
          .ftr {
            padding-bottom: max(16px, env(safe-area-inset-bottom));
          }
          .ctrl-inner {
            padding-left: max(12px, env(safe-area-inset-left));
            padding-right: max(12px, env(safe-area-inset-right));
          }
        }
      `}</style>
    </>
  );
}
