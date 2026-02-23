'use client';

import { useState } from 'react';

export default function SimpleLogin() {
    const [phone, setPhone] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        // Simple redirect without complex logic
        window.location.href = '/verify-otp';
    };

    return (
        <div style={{
            minHeight: '100vh',
            background: '#001f1f',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
        }}>
            <div style={{
                width: '100%',
                maxWidth: '400px',
                background: 'rgba(255,255,255,0.1)',
                padding: '40px',
                borderRadius: '20px',
                color: 'white'
            }}>
                <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>Wali Login</h1>
                
                <form onSubmit={handleSubmit}>
                    <input
                        type="tel"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="Enter phone number"
                        style={{
                            width: '100%',
                            padding: '15px',
                            marginBottom: '20px',
                            borderRadius: '10px',
                            border: 'none',
                            fontSize: '16px'
                        }}
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            width: '100%',
                            padding: '15px',
                            background: '#00b386',
                            color: 'white',
                            border: 'none',
                            borderRadius: '10px',
                            fontSize: '16px',
                            cursor: 'pointer'
                        }}
                    >
                        {loading ? 'Loading...' : 'Continue'}
                    </button>
                </form>
            </div>
        </div>
    );
}
