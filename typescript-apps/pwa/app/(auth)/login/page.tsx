'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, ChevronRight } from 'lucide-react';
import { LegalLinks } from '@/components/LegalLinks';

export default function LoginPage() {
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [phone, setPhone] = useState('');
    const [code, setCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [countdown, setCountdown] = useState(300);
    const [mounted, setMounted] = useState(false);

    // Dark mode color tokens (consistent with dashboard)
    const C = {
        pageBg: '#111827',
        cardBg: '#1F2937',
        cardBorder: 'rgba(255,255,255,0.08)',
        inputBg: '#374151',
        inputBorder: '#4B5563',
        green: '#059669',
        greenGlow: '0 0 15px rgba(5, 150, 105, 0.4)',
        greenGlowStrong: '0 0 20px rgba(5, 150, 105, 0.6)',
        logoGlow: '0 0 20px rgba(255,255,255,0.15)',
        textPrimary: '#F9FAFB',
        textSecondary: '#E5E7EB',
        textTertiary: '#9CA3AF',
        textSubtle: '#6B7280',
    };

    useEffect(() => { setMounted(true); }, []);

    useEffect(() => {
        if (step === 2 && countdown > 0) {
            const timer = setInterval(() => setCountdown(c => c - 1), 1000);
            return () => clearInterval(timer);
        }
    }, [step, countdown]);

    const handleSendOTP = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const phoneDigits = phone.replace(/\D/g, '');
            if (phoneDigits.length !== 10) throw new Error('Invalid number (10 digits required).');
            const fullPhone = '+225' + phoneDigits;
            const token = "mock-recaptcha-token-v3";
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/auth/send-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phoneNumber: fullPhone, recaptchaToken: token })
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Error sending code.');
            }
            setStep(2);
        } catch (err: any) {
            console.error('Auth Error:', err);
            setError(err.message || 'Connection error.');
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyOTP = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const phoneDigits = phone.replace(/\D/g, '');
            const fullPhone = '+225' + phoneDigits;
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/auth/verify-otp?phoneNumber=${encodeURIComponent(fullPhone)}&code=${code}`, {
                method: 'POST',
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Code incorrect.');
            }
            const data = await res.json();
            localStorage.setItem('wali_token', data.token);
            localStorage.setItem('user_role', 'artisan');
            router.push('/dashboard');
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Code incorrect ou expiré.');
        } finally {
            setLoading(false);
        }
    };

    if (!mounted) return (
        <div suppressHydrationWarning style={{ background: C.pageBg, minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ width: 32, height: 32, border: `3px solid ${C.green}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        </div>
    );

    return (
        <div suppressHydrationWarning style={{
            background: 'linear-gradient(180deg, #0F172A 0%, #111827 100%)',
            minHeight: '100vh',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            padding: '24px 16px',
        }}>
            {/* Float animation — plain style tag avoids styled-jsx hydration mismatch */}
            <style dangerouslySetInnerHTML={{
                __html: `
                @keyframes logoFloat {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-8px); }
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                .logo-float { animation: logoFloat 4s ease-in-out infinite; }
            ` }} />

            <div style={{ width: '100%', maxWidth: 360, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

                {/* ===== LOGO SECTION ===== */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 48 }}>
                    {/* Logo Container — white pops against dark */}
                    <div
                        className="logo-float"
                        style={{
                            width: 80, height: 80,
                            backgroundColor: '#FFFFFF',
                            borderRadius: 20,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            boxShadow: C.logoGlow,
                        }}
                    >
                        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                            <path d="M8 8 C8 8, 8 28, 20 32 C32 28, 32 8, 32 8" stroke="#059669" strokeWidth="5" strokeLinecap="round" fill="none" />
                        </svg>
                    </div>

                    {/* Brand Name */}
                    <h1 style={{
                        fontSize: 32, fontWeight: 700, color: C.textPrimary,
                        marginTop: 24, letterSpacing: '-0.5px',
                    }}>
                        wali
                    </h1>

                    {/* Tagline */}
                    <p style={{ fontSize: 16, color: C.textTertiary, marginTop: 8 }}>
                        Micro-assurance pour les artisans
                    </p>
                </div>

                {/* ===== INPUT CARD (DARK) ===== */}
                <div style={{
                    backgroundColor: C.cardBg,
                    border: `1px solid ${C.cardBorder}`,
                    borderRadius: 24,
                    padding: 32,
                    width: '100%',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                }}>
                    {step === 1 ? (
                        <form onSubmit={handleSendOTP}>
                            {/* Label */}
                            <label style={{
                                display: 'block', fontSize: 14, fontWeight: 500,
                                color: C.textSecondary, marginBottom: 8,
                            }}>
                                Numéro de téléphone
                            </label>

                            {/* Input (Dark) */}
                            <div style={{ position: 'relative', marginBottom: 20 }}>
                                <span style={{
                                    position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)',
                                    fontSize: 16, color: C.textTertiary, fontWeight: 500,
                                }}>+225</span>
                                <input
                                    type="tel"
                                    value={phone}
                                    onChange={e => {
                                        const v = e.target.value.replace(/\D/g, '').substring(0, 10);
                                        const parts = v.match(/.{1,2}/g) || [];
                                        setPhone(parts.join(' ').substring(0, 14));
                                    }}
                                    style={{
                                        width: '100%', height: 56, paddingLeft: 64, paddingRight: 16,
                                        backgroundColor: C.inputBg,
                                        border: `1px solid ${C.inputBorder}`,
                                        borderRadius: 12, fontSize: 16, color: C.textPrimary,
                                        outline: 'none', fontFamily: 'monospace',
                                        caretColor: C.green,
                                    }}
                                    placeholder="07 07 07 07 07"
                                    required
                                />
                            </div>

                            {/* Error */}
                            {error && (
                                <div style={{
                                    padding: 12, backgroundColor: 'rgba(239,68,68,0.1)',
                                    color: '#F87171', fontSize: 14, borderRadius: 8,
                                    border: '1px solid rgba(239,68,68,0.2)',
                                    marginBottom: 16,
                                }}>
                                    {error}
                                </div>
                            )}

                            {/* CTA Button with Green Glow */}
                            <button
                                type="submit"
                                disabled={loading}
                                style={{
                                    width: '100%', height: 56,
                                    backgroundColor: loading ? '#047857' : C.green,
                                    color: '#FFFFFF', fontSize: 16, fontWeight: 600,
                                    borderRadius: 12, border: 'none',
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                                    boxShadow: C.greenGlow,
                                    transition: 'all 0.2s',
                                    marginBottom: 16,
                                    opacity: loading ? 0.7 : 1,
                                }}
                                onMouseEnter={e => {
                                    if (!loading) {
                                        e.currentTarget.style.backgroundColor = '#047857';
                                        e.currentTarget.style.transform = 'translateY(-1px)';
                                        e.currentTarget.style.boxShadow = C.greenGlowStrong;
                                    }
                                }}
                                onMouseLeave={e => {
                                    e.currentTarget.style.backgroundColor = C.green;
                                    e.currentTarget.style.transform = 'translateY(0)';
                                    e.currentTarget.style.boxShadow = C.greenGlow;
                                }}
                            >
                                {loading ? <span>Envoi en cours...</span> : <span>Recevoir le code</span>}
                                {!loading && <ChevronRight size={20} />}
                            </button>

                            {/* Security Note */}
                            <div style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                            }}>
                                <Lock size={16} color={C.green} />
                                <span style={{ fontSize: 12, color: C.textSubtle }}>
                                    Vérifié par reCAPTCHA
                                </span>
                            </div>
                        </form>
                    ) : (
                        /* ===== OTP STEP (DARK) ===== */
                        <form onSubmit={handleVerifyOTP}>
                            <div style={{ textAlign: 'center', marginBottom: 24 }}>
                                <h2 style={{ fontSize: 20, fontWeight: 700, color: C.textPrimary }}>
                                    Code de vérification
                                </h2>
                                <p style={{ fontSize: 14, color: C.textTertiary, marginTop: 4 }}>
                                    Envoyé au +225 {phone}
                                </p>
                            </div>

                            <input
                                type="text"
                                value={code}
                                onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                style={{
                                    width: '100%', textAlign: 'center', fontSize: 28,
                                    fontFamily: 'monospace', letterSpacing: '0.3em',
                                    padding: '12px 0',
                                    border: 'none',
                                    borderBottom: `2px solid ${code.length === 6 ? C.green : C.inputBorder}`,
                                    outline: 'none', marginBottom: 24,
                                    backgroundColor: 'transparent', color: C.textPrimary,
                                    caretColor: C.green,
                                }}
                                placeholder="• • • • • •"
                                maxLength={6}
                                autoFocus
                            />

                            {error && (
                                <div style={{
                                    padding: 12, backgroundColor: 'rgba(239,68,68,0.1)',
                                    color: '#F87171', fontSize: 14, borderRadius: 8,
                                    border: '1px solid rgba(239,68,68,0.2)',
                                    marginBottom: 16,
                                }}>
                                    {error}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading || code.length !== 6}
                                style={{
                                    width: '100%', height: 56,
                                    backgroundColor: (loading || code.length !== 6) ? '#047857' : C.green,
                                    color: '#FFFFFF', fontSize: 16, fontWeight: 600,
                                    borderRadius: 12, border: 'none',
                                    cursor: (loading || code.length !== 6) ? 'not-allowed' : 'pointer',
                                    boxShadow: code.length === 6 ? C.greenGlow : 'none',
                                    opacity: (loading || code.length !== 6) ? 0.5 : 1,
                                    transition: 'all 0.2s',
                                }}
                            >
                                <span>{loading ? 'Vérification...' : 'Confirmer'}</span>
                            </button>

                            <button
                                type="button"
                                onClick={() => { setStep(1); setCode(''); setError(''); }}
                                style={{
                                    width: '100%', marginTop: 16, fontSize: 14,
                                    color: C.textSubtle, background: 'none', border: 'none',
                                    cursor: 'pointer',
                                }}
                            >
                                <span>Changer de numéro</span>
                            </button>
                        </form>
                    )}

                    {/* Register Link */}
                    {step === 1 && (
                        <div style={{ marginTop: 24, textAlign: 'center' }}>
                            <button
                                onClick={() => router.push('/register')}
                                style={{
                                    background: 'none', border: 'none', cursor: 'pointer',
                                    fontSize: 14, color: C.green, fontWeight: 600,
                                }}
                            >
                                Pas encore de compte ? Créer un compte
                            </button>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <LegalLinks />

                <div style={{ marginTop: 32, textAlign: 'center', fontSize: 13, color: C.textTertiary }}>
                    <p style={{ marginBottom: 8, fontWeight: 500, color: C.textSecondary }}>
                        Besoin d&apos;aide ? <a href="mailto:support@wali.ci" style={{ color: C.textPrimary, textDecoration: 'underline' }}>Contactez-nous</a>
                    </p>
                    <p>© 2025 Wali. Tous droits réservés.</p>
                </div>
            </div>
        </div>
    );
}
