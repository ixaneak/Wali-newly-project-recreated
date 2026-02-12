"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import PartnerDisclosure from '@/components/auth/PartnerDisclosure';
import { Smartphone, ChevronRight } from 'lucide-react';

export default function RegisterPage() {
    const router = useRouter();
    const [step, setStep] = useState<'disclosure' | 'phone' | 'otp'>('disclosure');
    const [phone, setPhone] = useState('');

    const handleDisclosureAccepted = () => {
        setStep('phone');
    };

    const handlePhoneSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // Here we would trigger OTP logic (same as login)
        // For MVP refactor, just mock next step
        setStep('otp');
    };

    // ... Using simplified flow for brevity, similar to login/page.tsx but with Disclosure step first

    return (
        <div className="min-h-screen relative overflow-hidden flex items-center justify-center p-4 bg-gray-50 dark:bg-slate-950">
            {step === 'disclosure' && (
                <div className="w-full max-w-md animate-fade-in">
                    <PartnerDisclosure onAccept={handleDisclosureAccepted} />
                </div>
            )}

            {step === 'phone' && (
                <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl shadow-xl p-8 animate-slide-up">
                    <h2 className="text-2xl font-bold mb-6 text-center text-gray-900 dark:text-white">Créer un compte</h2>
                    <form onSubmit={handlePhoneSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                Numéro de téléphone
                            </label>
                            <div className="relative h-14">
                                <div className="absolute left-0 top-0 bottom-0 flex items-center pl-4 gap-3 bg-gray-50 dark:bg-slate-800 rounded-l-xl border-y border-l border-gray-200 dark:border-slate-700">
                                    <span className="text-xl">🇨🇮</span>
                                    <span className="font-semibold text-gray-700 dark:text-gray-300">+225</span>
                                </div>
                                <input
                                    type="tel"
                                    value={phone}
                                    onChange={(e) => setPhone(e.target.value)}
                                    placeholder="XX XX XX XX XX"
                                    className="w-full h-full pl-[6.5rem] pr-4 bg-white dark:bg-slate-900 border-2 border-gray-200 dark:border-slate-700 rounded-xl focus:border-emerald-500 focus:ring-0 outline-none transition font-mono text-lg"
                                    required
                                />
                            </div>
                        </div>
                        <button type="submit" className="w-full h-14 bg-emerald-600 text-white rounded-xl font-bold">
                            Envoyer le code
                        </button>
                    </form>
                </div>
            )}

            {step === 'otp' && (
                <div className="text-center">
                    <p>OTP Mock Step - Registration Logic via API Client would go here.</p>
                </div>
            )}
        </div>
    );
}
