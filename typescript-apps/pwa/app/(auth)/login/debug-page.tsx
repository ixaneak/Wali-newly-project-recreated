'use client';

import { useEffect, useState } from 'react';

export default function DebugLoginPage() {
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    try {
      setMounted(true);
      console.log('Debug page mounted successfully');
    } catch (err: any) {
      setError(err.message);
      console.error('Mount error:', err);
    }
  }, []);

  if (error) {
    return (
      <div style={{ padding: '20px', color: 'red', background: 'white' }}>
        <h1>Error:</h1>
        <pre>{error}</pre>
      </div>
    );
  }

  if (!mounted) {
    return <div style={{ color: 'white', padding: '20px' }}>Mounting...</div>;
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: '#001f1f',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      fontFamily: 'sans-serif'
    }}>
      <div style={{
        padding: '40px',
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '20px',
        textAlign: 'center'
      }}>
        <h1>Debug Page Works!</h1>
        <p>If you can see this, the issue is with the original component.</p>
        <button 
          onClick={() => window.location.href = '/login'}
          style={{
            marginTop: '20px',
            padding: '12px 24px',
            background: '#00b386',
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            cursor: 'pointer'
          }}
        >
          Go to Real Login
        </button>
      </div>
    </div>
  );
}
