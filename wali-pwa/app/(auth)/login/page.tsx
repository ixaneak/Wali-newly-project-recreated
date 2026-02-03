'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Smartphone, Lock, ChevronRight } from 'lucide-react';
import { notificationService } from '@/lib/api-client';

import { auth } from '@/lib/firebase';
import { RecaptchaVerifier, signInWithPhoneNumber, ConfirmationResult } from 'firebase/auth';

declare global {
    interface Window {
        recaptchaVerifier: any;
    }
}

export default function LoginPage() {
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [phone, setPhone] = useState('');
    const [code, setCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [countdown, setCountdown] = useState(300);
    const [confirmationResult, setConfirmationResult] = useState<ConfirmationResult | null>(null);

    // Initialize recaptcha
    useEffect(() => {
        if (!window.recaptchaVerifier) {
            window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
                'size': 'invisible',
                'callback': (response: any) => {
                    // reCAPTCHA solved, allow signInWithPhoneNumber.
                }
            });
        }
    }, []);

    // Countdown timer logic
    useEffect(() => {
        if (step === 2 && countdown > 0) {
            const timer = setInterval(() => {
                setCountdown((prev) => prev - 1);
            }, 1000);
            return () => clearInterval(timer);
        }
    }, [step, countdown]);

    // Phone formatting: Auto-space every 2 digits
    const formatPhoneNumber = (value: string) => {
        const numbers = value.replace(/\D/g, '');
        const parts = numbers.match(/.{1,2}/g) || [];
        return parts.join(' ').substring(0, 14); // XX XX XX XX XX
    };

    const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const formatted = formatPhoneNumber(e.target.value);
        setPhone(formatted);
    };

    const handleSendOTP = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const fullPhone = '+225' + phone.replace(/\s/g, '');
            const appVerifier = window.recaptchaVerifier;

            const confirmation = await signInWithPhoneNumber(auth, fullPhone, appVerifier);
            setConfirmationResult(confirmation);
            setStep(2);
            setCountdown(300);
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Erreur de connexion.');
            if (window.recaptchaVerifier) {
                window.recaptchaVerifier.clear();
                // Re-initialize might be needed depending on error, but usually clear is enough to retry
            }
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyOTP = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (confirmationResult) {
                await confirmationResult.confirm(code);
                router.push('/dashboard');
            } else {
                setError("Erreur de session. Veuillez réessayer.");
            }
        } catch (err: any) {
            setError('Code incorrect ou expiré.');
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="min-h-screen relative overflow-hidden flex items-center justify-center p-4 animate-gradient">

            {/* Floating Leaves Animation */}
            <div className="absolute inset-0 pointer-events-none">
                {['🍃', '🍂', '🌿', '🍃', '🍂'].map((leaf, i) => (
                    <div
                        key={i}
                        className="absolute text-4xl animate-float-leaf"
                        style={{
                            left: `${20 + i * 15}%`,
                            animationDelay: `${i * 3}s`,
                            top: '100%',
                            opacity: 0,
                            filter: 'blur(0.5px)'
                        }}
                    >
                        {leaf}
                    </div>
                ))}
            </div>

            {/* Main Container */}
            <div className="relative z-10 w-full max-w-md flex flex-col items-center">

                {/* Logo Section */}
                <div className="bg-white rounded-3xl w-24 h-24 flex items-center justify-center mb-6 animate-logo-glow">
                    <svg width="60" height="60" viewBox="0 0 100 100">
                        <defs>
                            <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#34d399" />
                                <stop offset="50%" stopColor="#10b981" />
                                <stop offset="100%" stopColor="#059669" />
                            </linearGradient>
                        </defs>
                        <path
                            d="M10 20 Q10 10 20 10 L35 10 Q45 10 45 20 L45 40 Q45 50 50 50 Q55 50 55 40 L55 20 Q55 10 65 10 L80 10 Q90 10 90 20 L90 70 Q90 90 70 90 L60 90 Q50 90 50 80 Q50 90 40 90 L30 90 Q10 90 10 70 Z"
                            fill="url(#logoGradient)"
                        />
                    </svg>
                </div>

                <div className="text-center mb-8">
                    <h1 className="text-5xl font-bold text-white mb-2 tracking-tight">wali</h1>
                    <p className="text-emerald-50 text-lg font-light">Micro-assurance pour artisans</p>
                </div>

                {/* Login Card */}
                <div className="w-full bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-6 sm:p-8">

                    {step === 1 ? (
                        <>
                            <div className="mb-8">
                                <div className="flex items-center gap-2 mb-2">
                                    <Smartphone className="w-6 h-6 text-emerald-600" />
                                    <h2 className="text-xl font-bold text-gray-800">Connexion sécurisée</h2>
                                </div>
                                <p className="text-gray-500 text-sm">Entrez votre numéro pour recevoir un code OTP</p>
                            </div>

                            <form onSubmit={handleSendOTP} className="space-y-6">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-2 ml-1">
                                        Numéro de téléphone
                                    </label>
                                    <div className="relative h-14">
                                        <div className="absolute left-0 top-0 bottom-0 flex items-center pl-4 gap-3 bg-gray-50 rounded-l-xl border-y border-l border-gray-200">
                                            <span className="text-xl">🇨🇮</span>
                                            <span className="font-semibold text-gray-700">+225</span>
                                        </div>
                                        <input
                                            type="tel"
                                            value={phone}
                                            onChange={handlePhoneChange}
                                            placeholder="XX XX XX XX XX"
                                            className="w-full h-full pl-[6.5rem] pr-4 bg-white border-2 border-gray-200 rounded-xl focus:border-emerald-500 focus:ring-0 outline-none transition font-mono text-lg text-gray-800 placeholder-gray-300"
                                            required
                                        />
                                    </div>
                                </div>

                                {error && (
                                    <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm font-medium flex items-center gap-2 animate-pulse">
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        {error}
                                    </div>
                                )}

                                <button
                                    type="submit"
                                    disabled={loading || phone.replace(/\s/g, '').length !== 10}
                                    style={{
                                        background: 'linear-gradient(to right, #10b981, #0d9488)',
                                        boxShadow: '0 10px 15px -3px rgba(16, 185, 129, 0.3)'
                                    }}
                                    className="w-full h-14 text-white rounded-xl font-semibold text-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                >
                                    {loading ? 'Envoi...' : 'Recevoir le code OTP'}
                                    {!loading && <ChevronRight className="w-5 h-5" />}
                                </button>

                                <div className="flex items-center gap-2 justify-center text-xs text-gray-500 bg-gray-50 py-2 rounded-lg">
                                    <Lock className="w-3 h-3 text-emerald-600" />
                                    <span>Connexion sécurisée par code à usage unique</span>
                                </div>

                                <div className="relative py-2">
                                    <div className="absolute inset-0 flex items-center">
                                        <div className="w-full border-t border-gray-200"></div>
                                    </div>
                                    <div className="relative flex justify-center text-sm">
                                        <span className="px-4 bg-white text-gray-400 font-medium">ou</span>
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    className="w-full h-12 bg-white border-2 border-gray-200 text-gray-600 rounded-xl font-semibold hover:bg-gray-50 hover:border-gray-300 transition"
                                >
                                    Créer un compte
                                </button>

                                <div className="text-center space-y-2">
                                    <p className="text-xs text-gray-400 leading-relaxed">
                                        En vous connectant, vous acceptez nos{' '}
                                        <a href="/terms" className="text-emerald-600 font-medium hover:underline">conditions d'utilisation</a>
                                        {' '}et notre{' '}
                                        <a href="/privacy" className="text-emerald-600 font-medium hover:underline">politique de confidentialité</a>
                                    </p>
                                </div>
                            </form>
                            <div id="recaptcha-container"></div>
                        </>
                    ) : (
                        /* OTP Step */
                        <>
                            <div className="text-center mb-8">
                                <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-100">
                                    <Lock className="w-8 h-8 text-emerald-600" />
                                </div>
                                <h2 className="text-xl font-bold text-gray-800 mb-2">Code envoyé</h2>
                                <div className="flex items-center justify-center gap-2 text-gray-600 mb-1">
                                    <Smartphone className="w-4 h-4" />
                                    <span className="text-sm font-medium">+225 {phone}</span>
                                </div>
                                <p className="text-3xl font-bold text-emerald-600 font-mono mt-4">{formatTime(countdown)}</p>
                            </div>

                            <form onSubmit={handleVerifyOTP} className="space-y-6">
                                <div>
                                    <input
                                        type="text"
                                        value={code}
                                        onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                        placeholder="• • • • • •"
                                        maxLength={6}
                                        className="w-full h-16 text-center text-3xl font-mono tracking-[0.5em] border-2 border-gray-200 rounded-xl focus:border-emerald-500 focus:ring-0 outline-none transition text-gray-800 placeholder-gray-300"
                                        required
                                        autoFocus
                                    />
                                </div>

                                {error && (
                                    <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm font-medium flex items-center gap-2 animate-pulse">
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        {error}
                                    </div>
                                )}

                                <button
                                    type="submit"
                                    disabled={loading || code.length !== 6}
                                    style={{
                                        background: 'linear-gradient(to right, #10b981, #0d9488)',
                                        boxShadow: '0 10px 15px -3px rgba(16, 185, 129, 0.3)'
                                    }}
                                    className="w-full h-14 text-white rounded-xl font-semibold text-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? 'Vérification...' : 'Se connecter'}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setStep(1);
                                        setCode('');
                                        setError('');
                                    }}
                                    className="w-full text-gray-500 font-medium hover:text-gray-700 text-sm py-2 transition"
                                >
                                    ← Modifier le numéro
                                </button>
                            </form>
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="mt-8 text-center space-y-2">
                    <p className="text-emerald-100 text-sm">
                        Besoin d'aide ?{' '}
                        <a href="/support" className="text-white hover:underline font-medium">Contactez-nous</a>
                    </p>
                    <p className="text-emerald-200/60 text-xs">© 2025 Wali. Tous droits réservés.</p>
                </div>
            </div>
        </div>
    );
}
