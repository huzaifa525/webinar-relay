'use client';

export default function OfflinePage() {
  return (
    <div style={{
      minHeight: '100dvh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0b0e1a',
      color: '#fff',
      fontFamily: 'Inter, system-ui, sans-serif',
      padding: '24px 16px',
      textAlign: 'center' as const,
    }}>
      <div style={{
        width: 72, height: 72, borderRadius: '50%',
        background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: 20, fontSize: 28, color: 'rgba(212,175,55,0.5)',
      }}>
        <i className="fas fa-wifi-slash" />
      </div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>You&apos;re Offline</h1>
      <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.45)', maxWidth: 320, lineHeight: 1.6 }}>
        Check your internet connection and try again. The app will reconnect automatically.
      </p>
      <button
        onClick={() => window.location.reload()}
        style={{
          marginTop: 24, padding: '14px 32px',
          background: 'linear-gradient(135deg, #d4af37, #b39128)',
          border: 'none', borderRadius: 10, color: '#fff',
          fontSize: 15, fontWeight: 600, cursor: 'pointer',
          minHeight: 48,
        }}
      >
        Retry
      </button>
    </div>
  );
}
