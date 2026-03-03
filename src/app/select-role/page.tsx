import { Suspense } from 'react';
import RoleSelection from '@/components/RoleSelection';

export default function SelectRolePage() {
  return (
    <Suspense fallback={
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(180deg, #090d1b 0%, #0a0f22 50%, #090d1b 100%)',
      }}>
        <div style={{
          width: 44,
          height: 44,
          borderRadius: '50%',
          border: '3px solid rgba(212, 175, 55, 0.15)',
          borderTopColor: '#d4af37',
          animation: 'spin 1s linear infinite',
        }} />
      </div>
    }>
      <RoleSelection />
    </Suspense>
  );
}
