'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';

// Translation data (Subset for OTP)
const translations = {
    fr: {
        tagline: "Micro-assurance pour les artisans",
        otpLabel: "Code de vérification",
        confirm: "Confirmer",
        verifying: "Vérification...",
        resend: "Renvoyer le code",
        back: "Retour",
        connectionProblem: "Problème de connexion ?",
        captcha: "Vérifié par reCAPTCHA",
        needHelp: "Besoin d'aide ?",
        contactUs: "Contactez nous",
        rights: "Tous droits réservés.",
    },
    en: {
        tagline: "Micro-insurance for artisans",
        otpLabel: "Verification code",
        confirm: "Confirm",
        verifying: "Verifying...",
        resend: "Resend code",
        back: "Back",
        connectionProblem: "Connection trouble?",
        captcha: "Protected by reCAPTCHA",
        needHelp: "Need help?",
        contactUs: "Contact us",
        rights: "All rights reserved.",
    },
    dyu: {
        tagline: "Kɔlɔsɔli fitini ni ɲɔgɔn cɛ",
        otpLabel: "Kode",
        confirm: "Sɔn",
        verifying: "Kɔlɔsɔli...",
        resend: "Kode ci abada",
        back: "Kɔ",
        connectionProblem: "Connection problematic ?",
        captcha: "reCAPTCHA yɛrɛmahɔrɔnya",
        needHelp: "Dɛmɛ sɔrɔ ?",
        contactUs: "Anw bɛ wele",
        rights: "Koloma bɛɛ ka kan.",
    },
    bci: {
        tagline: "Assurance ndɛn ndɛn mɛn denlɛ",
        otpLabel: "Code",
        confirm: "Jɔ",
        verifying: "Sɛ...",
        resend: "Code wlɛ",
        back: "Sɛ",
        connectionProblem: "Connection ɛn ɛ kɔnɔ ?",
        captcha: "reCAPTCHA sɛ",
        needHelp: "Bɛ dɛ ?",
        contactUs: "Bɛ wa wlɛ",
        rights: "Copyright 2025 Wali.",
    }
};

type LangKey = keyof typeof translations;

function VerifyOtpContent() {
    const [otp, setOtp] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [lang, setLang] = useState<LangKey>('fr');
    const [isLowPower, setIsLowPower] = useState(false);
    const router = useRouter();
    const searchParams = useSearchParams();
    const isTestMode = searchParams.get('testMode') === 'true';

    // Test Mode: Kill Animations & Auto-Fill
    useEffect(() => {
        if (isTestMode) {
            const style = document.createElement('style');
            style.textContent = `
        *,*::before,*::after{animation-duration:0.001s!important;transition-duration:0.001s!important}
        .bg-container,.wave,.particle,.glow{display:none!important}
        .login-card{animation:none!important;opacity:1!important;transform:none!important}
      `;
            document.head.appendChild(style);

            // Auto-fill logic
            setTimeout(() => {
                setOtp('123456');
                // Auto-submit after fill
                setTimeout(() => {
                    document.querySelector<HTMLButtonElement>('[data-testid="verify-otp"]')?.click();
                }, 100);
            }, 500);
        }
    }, [isTestMode]);

    useEffect(() => {
        const isLowEnd = navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4;
        const isOldPhone = /Android [1-4]|iPhone OS [1-9]|iOS [1-9]/.test(navigator.userAgent);
        setIsLowPower(isLowEnd || isOldPhone);

        const savedLang = localStorage.getItem('wali-lang') as LangKey;
        if (savedLang && translations[savedLang]) {
            setLang(savedLang);
        }
    }, []);

    const t = translations[lang];

    const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value.replace(/\D/g, '').slice(0, 6);
        setOtp(val);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (otp.length !== 6) return;

        setIsLoading(true);
        // Simulate API call
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // Redirect to Dashboard
        router.push('/dashboard');
    };

    return (
        <>
            <style>{`
         /* Reusing styles from login page - ideally this should be a shared component or global css */
         /* For brevity, including minimal necessary CSS or relying on tailwind */
        .wave {
            animation: wave-move 20s ease-in-out infinite;
        }
        @keyframes wave-move {
            0%, 100% { transform: translateX(0) translateY(0) rotate(-5deg); }
            50% { transform: translateX(10%) translateY(0) rotate(-5deg); }
        }
      `}</style>
            <div className={`min-h-screen min-h-[100dvh] flex items-center justify-center relative overflow-hidden`} style={{ background: '#001f1f' }}>

                {/* Animated Background (Simplified) */}
                {!isTestMode && !isLowPower && (
                    <div className="fixed inset-0 -z-10 overflow-hidden">
                        <div className="wave absolute w-[200%] h-full opacity-50 bg-[#00d9a3]/10 -top-[20%] -left-[50%]" />
                        <div className="wave absolute w-[200%] h-full opacity-30 bg-[#009688]/20 top-[20%] -left-[30%]" />
                    </div>
                )}

                <div
                    className="login-card w-[90%] max-w-[380px] rounded-3xl p-6 sm:p-8 z-10"
                    style={{
                        background: 'rgba(15, 35, 35, 0.95)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.12)',
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                    }}
                >
                    {/* Logo */}
                    <div className="text-center mb-6">
                        <div className="w-[72px] h-[72px] inline-flex items-center justify-center mb-4">
                            <svg viewBox="0 0 48 48" fill="none" className="w-full h-full">
                                <rect x="2" y="2" width="44" height="44" rx="14" fill="white" />
                                <path d="M12 28 Q18 16 24 22 Q30 16 36 28" stroke="#00b386" strokeWidth="5.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                            </svg>
                        </div>
                        <h1 className="text-white text-2xl font-semibold mb-1.5">wali</h1>
                        <p className="text-white/70 text-sm">{t.tagline}</p>
                    </div>

                    <form onSubmit={handleSubmit}>
                        <div className="mb-5">
                            <label className="block text-white/90 text-sm font-medium mb-2 ml-1">{t.otpLabel}</label>
                            <input
                                type="text"
                                data-testid="otp-input"
                                value={otp}
                                onChange={handleOtpChange}
                                placeholder="• • • • • •"
                                maxLength={6}
                                inputMode="numeric"
                                autoComplete="one-time-code"
                                className="w-full px-4 py-4 rounded-xl text-white text-base outline-none text-center tracking-[0.5em] font-mono text-xl"
                                style={{
                                    background: 'rgba(255, 255, 255, 0.12)',
                                    border: '1px solid rgba(255, 255, 255, 0.15)',
                                }}
                                autoFocus
                            />
                        </div>

                        <button
                            type="submit"
                            data-testid="verify-otp"
                            disabled={isLoading || otp.length < 6}
                            className="w-full py-4 rounded-xl text-white font-semibold flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50"
                            style={{
                                background: 'linear-gradient(135deg, #00b386 0%, #00d9a3 100%)',
                                boxShadow: '0 4px 15px rgba(0, 179, 134, 0.4)',
                            }}
                        >
                            {isLoading ? t.verifying : t.confirm}
                        </button>

                        <button
                            type="button"
                            onClick={() => router.back()}
                            className="w-full mt-4 text-white/60 text-sm hover:text-white"
                        >
                            {t.back}
                        </button>
                    </form>

                    {/* Footer */}
                    <div className="mt-8 text-center text-white/45 text-xs">
                        <div className="flex items-center justify-center gap-1.5 mb-3">
                            {t.captcha}
                        </div>
                        <p>© 2025 Wali. {t.rights}</p>
                    </div>
                </div>
            </div>
        </>
    );
}

export default function VerifyOtpPage() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-white">Loading...</div>}>
            <VerifyOtpContent />
        </Suspense>
    );
}
