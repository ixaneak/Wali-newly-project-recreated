'use client';

import { useState, useEffect, Suspense } from 'react';
import { AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import StartupAnimation from '@/components/auth/StartupAnimation';
import LegalLinks from '@/components/LegalLinks';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import { useLanguage } from '@/components/LanguageProvider';

// Separate component that uses useSearchParams
function LoginContent() {
    const { t } = useLanguage();
    const [phone, setPhone] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showHelp, setShowHelp] = useState(false);
    const [mounted, setMounted] = useState(false);
    const searchParams = useSearchParams();
    const isTestMode = searchParams?.get('testMode') === 'true';
    const [showSplash, setShowSplash] = useState(!isTestMode);

    useEffect(() => {
        setMounted(true);

        // Test Mode: Kill Animations
        if (isTestMode) {
            const style = document.createElement('style');
            style.textContent = `
        *,*::before,*::after{animation:none!important;transition:none!important}
        .bg-container,.wave,.particle,.glow{display:none!important}
      `;
            document.head.appendChild(style);
        }
    }, [isTestMode]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (phone.replace(/\D/g, '').length < 10) return;
        setIsLoading(true);
        await new Promise((resolve) => setTimeout(resolve, 1500));
        setIsLoading(false);
        window.location.href = `/verify-otp${isTestMode ? '?testMode=true' : ''}`;
    };

    if (!mounted) {
        return <div style={{ color: 'white', textAlign: 'center', padding: '20px' }}>Chargement...</div>;
    }

    return (
        <>
            <AnimatePresence mode="wait">
                {showSplash && <StartupAnimation onComplete={() => setShowSplash(false)} />}
            </AnimatePresence>

            {/* Global CSS */}
            <style>{`
        @keyframes wave-move {
          0%, 100% { transform: translateX(0) translateY(0) rotate(-5deg); }
          50% { transform: translateX(10%) translateY(0) rotate(-5deg); }
        }
        @keyframes pulse-glow {
          0%, 100% { opacity: 0.25; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.1); }
        }
        @keyframes card-enter {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

            <div style={{
                minHeight: '100vh',
                background: '#001f1f',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
                position: 'relative',
                overflow: 'hidden'
            }}>
                <LanguageSwitcher />

                {/* Animated Background */}
                {!isTestMode && (
                    <>
                        <div style={{
                            position: 'absolute',
                            inset: 0,
                            background: 'linear-gradient(135deg, #001a1a 0%, #002a2a 50%, #001f1f 100%)',
                            zIndex: -1
                        }} />
                        {/* Waves */}
                        <div style={{
                            position: 'absolute',
                            width: '200%',
                            height: '100%',
                            opacity: 0.3,
                            background: 'linear-gradient(90deg, transparent, rgba(0,217,163,0.1), transparent)',
                            filter: 'blur(40px)',
                            top: '-20%',
                            left: '-50%',
                            animation: 'wave-move 20s ease-in-out infinite',
                            zIndex: -1
                        }} />
                        {/* Glow */}
                        <div style={{
                            position: 'absolute',
                            width: 300,
                            height: 300,
                            borderRadius: '50%',
                            background: 'radial-gradient(circle, rgba(0,217,163,0.3), transparent)',
                            top: '20%',
                            left: '10%',
                            animation: 'pulse-glow 8s ease-in-out infinite',
                            zIndex: -1
                        }} />
                    </>
                )}

                {/* Login Card */}
                <div style={{
                    width: '100%',
                    maxWidth: '380px',
                    background: 'rgba(15, 35, 35, 0.95)',
                    backdropFilter: 'blur(20px)',
                    borderRadius: '24px',
                    padding: '32px',
                    border: '1px solid rgba(255,255,255,0.12)',
                    boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
                    animation: 'card-enter 0.6s ease-out',
                    zIndex: 10
                }}>
                    {/* Logo */}
                    <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                        <svg viewBox="0 0 48 48" style={{ width: '72px', height: '72px', margin: '0 auto 16px', filter: 'drop-shadow(0 4px 20px rgba(0,217,163,0.3))' }}>
                            <rect x="2" y="2" width="44" height="44" rx="14" fill="white" />
                            <path d="M12 28 Q18 16 24 28 Q30 16 36 28" stroke="#00b386" strokeWidth="5.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                        </svg>
                        <h1 style={{ color: 'white', fontSize: '28px', fontWeight: 600, marginBottom: '8px' }}>wali</h1>
                        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>{t('slogan')}</p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit}>
                        <div style={{ marginBottom: '20px' }}>
                            <label style={{
                                display: 'block',
                                color: 'rgba(255,255,255,0.9)',
                                fontSize: '14px',
                                fontWeight: 500,
                                marginBottom: '8px'
                            }}>
                                {t('phone_label')}
                            </label>
                            <input
                                type="tel"
                                value={phone}
                                onChange={(e) => setPhone(e.target.value)}
                                placeholder={t('placeholder')}
                                style={{
                                    width: '100%',
                                    padding: '16px',
                                    background: 'rgba(255,255,255,0.12)',
                                    border: '1px solid rgba(255,255,255,0.15)',
                                    borderRadius: '12px',
                                    color: 'white',
                                    fontSize: '16px',
                                    outline: 'none',
                                }}
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            style={{
                                width: '100%',
                                padding: '16px',
                                background: 'linear-gradient(135deg, #00b386 0%, #00d9a3 100%)',
                                border: 'none',
                                borderRadius: '12px',
                                color: 'white',
                                fontSize: '16px',
                                fontWeight: 600,
                                cursor: isLoading ? 'not-allowed' : 'pointer',
                                opacity: isLoading ? 0.6 : 1,
                            }}
                        >
                            {isLoading ? t('button_sending') : t('button_send')}
                        </button>
                    </form>

                    {/* Help Section */}
                    <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                        <button
                            type="button"
                            onClick={() => setShowHelp(!showHelp)}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(77, 171, 247, 0.1)',
                                border: '1px solid rgba(77, 171, 247, 0.3)',
                                borderRadius: '10px',
                                color: '#4dabf7',
                                fontSize: '14px',
                                cursor: 'pointer',
                            }}
                        >
                            {t('help_button')}
                        </button>

                        {showHelp && (
                            <div style={{
                                marginTop: '16px',
                                padding: '16px',
                                background: 'rgba(77, 171, 247, 0.05)',
                                borderRadius: '12px',
                                border: '1px solid rgba(77, 171, 247, 0.15)'
                            }}>
                                <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '13px', fontWeight: 600, marginBottom: '12px' }}>
                                    {t('help_title')}
                                </p>
                                <a
                                    href="https://wa.me/22500000000"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '10px',
                                        padding: '12px',
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '10px',
                                        color: 'white',
                                        textDecoration: 'none',
                                    }}
                                >
                                    <span>💬</span>
                                    <div>
                                        <div style={{ fontSize: '13px', fontWeight: 500 }}>{t('contact_support')}</div>
                                        <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>WhatsApp</div>
                                    </div>
                                </a>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div style={{ marginTop: '20px', textAlign: 'center' }}>
                        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px' }}>
                            {t('no_account')} <Link href="/register" style={{ color: 'rgba(255,255,255,0.85)' }}>{t('create_account')}</Link>
                        </p>
                        <LegalLinks />
                        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '11px', marginTop: '8px' }}>
                            {t('copyright')}
                        </p>
                    </div>
                </div>
            </div>
        </>
    );
}

// Main page with Suspense
export default function LoginPage() {
    return (
        <Suspense fallback={
            <div style={{
                minHeight: '100vh',
                background: '#001f1f',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white'
            }}>
                Chargement...
            </div>
        }>
            <LoginContent />
        </Suspense>
    );
}
