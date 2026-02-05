"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Stethoscope, Lock, ArrowRight, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { ThemeToggle } from '@/components/theme-toggle';

export default function PharmacyLoginPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        // Simulate API Login
        setTimeout(() => {
            if (email === 'pharmacie@wali.com' && password === 'pharma123') {
                localStorage.setItem('user_role', 'pharmacy');
                toast.success('Connexion réussie');
                router.push('/pharmacy/dashboard');
            } else {
                toast.error('Identifiants incorrects');
                setLoading(false);
            }
        }, 1500);
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
            <div className="absolute top-4 right-4">
                <ThemeToggle />
            </div>

            <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl shadow-xl overflow-hidden border border-gray-100 dark:border-slate-800">
                {/* Header */}
                <div className="bg-emerald-600 p-8 text-center relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/medical-icons.png')] opacity-10"></div>
                    <div className="relative z-10 flex flex-col items-center">
                        <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mb-4 shadow-lg">
                            <Stethoscope className="w-8 h-8 text-emerald-600" />
                        </div>
                        <h1 className="text-2xl font-bold text-white">Espace Pharmacie</h1>
                        <p className="text-emerald-100 text-sm mt-1">Portail Partenaires Wali</p>
                    </div>
                </div>

                {/* Login Form */}
                <div className="p-8">
                    <form onSubmit={handleLogin} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 ml-1">
                                Identifiant Pharmacie
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-gray-900 dark:text-white"
                                placeholder="pharmacie@wali.com"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 ml-1">
                                Mot de passe
                            </label>
                            <div className="relative">
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-gray-900 dark:text-white"
                                    placeholder="••••••••"
                                    required
                                />
                                <Lock className="absolute right-4 top-3.5 text-gray-400 w-5 h-5" />
                            </div>
                        </div>

                        <div className="flex items-center justify-between text-sm">
                            <label className="flex items-center gap-2 text-gray-600 dark:text-gray-400 cursor-pointer">
                                <input type="checkbox" className="w-4 h-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500 bg-gray-50 dark:bg-slate-800" />
                                Se souvenir de moi
                            </label>
                            <a href="#" className="font-medium text-emerald-600 hover:text-emerald-500">
                                Mot de passe oublié ?
                            </a>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-lg shadow-emerald-200 dark:shadow-emerald-900/20 active:scale-[0.98] transition flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    Se connecter
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-xs text-gray-400 leading-relaxed">
                            En vous connectant, vous acceptez nos{' '}
                            <a href="/legal/terms" className="text-[#0D9488] font-medium hover:underline">conditions d&apos;utilisation</a>
                            {' '}et notre{' '}
                            <a href="/legal/privacy" className="text-[#0D9488] font-medium hover:underline">politique de confidentialité</a>
                        </p>
                    </div>

                    <div className="mt-4 text-center">
                        <p className="text-xs text-gray-400">
                            En cas de problème technique, contactez le support Wali au <span className="font-medium text-gray-600 dark:text-gray-300">27 22 55 44 00</span>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
