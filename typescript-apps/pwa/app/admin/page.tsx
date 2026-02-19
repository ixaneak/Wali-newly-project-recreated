'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck, Mail, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { adminAuth } from '@/lib/api-client';

export default function AdminLoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Check if already logged in
    useEffect(() => {
        const checkAuth = async () => {
            const hasToken = document.cookie.includes('wali_auth_token=');
            if (hasToken) {
                const isValid = await adminAuth.verifyToken();
                if (isValid) {
                    router.push('/admin/dash');
                }
            }
        };
        checkAuth();
    }, [router]);

    const setAuthCookie = (token: string) => {
        // Set cookie with proper attributes for middleware
        // Expires in 12 hours (0.5 days)
        const expires = new Date(Date.now() + 12 * 60 * 60 * 1000).toUTCString();
        const secure = window.location.protocol === 'https:' ? 'Secure;' : '';
        const sameSite = 'Strict';
        
        document.cookie = `wali_auth_token=${token}; expires=${expires}; path=/; ${secure} SameSite=${sameSite}`;
    };

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const data = await adminAuth.login(email, password);

            // Set auth cookie for middleware (12 hours)
            setAuthCookie(data.access_token);

            // Also store minimal info in localStorage for UI
            localStorage.setItem('admin_user', JSON.stringify({
                id: data.user.id,
                email: data.user.email,
                name: data.user.name || data.user.email,
                role: data.user.role
            }));

            toast.success('Bienvenue, Administrateur');
            router.push('/admin/dash');
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.response?.data?.message || 'Identifiants incorrects';
            setError(errorMessage);
            toast.error(errorMessage);
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 relative overflow-hidden">
            {/* Animated Background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-emerald-900/10 rounded-full blur-3xl transform -translate-y-1/2 animate-pulse" />
                <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-blue-900/10 rounded-full blur-3xl transform translate-y-1/2 animate-pulse" style={{ animationDelay: '1s' }} />
            </div>

            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl relative overflow-hidden">
                {/* Top decorative bar */}
                <div className="h-1.5 bg-gradient-to-r from-emerald-500 via-teal-500 to-blue-500 w-full" />

                <div className="p-8">
                    {/* Logo */}
                    <div className="text-center mb-8">
                        <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-inner ring-1 ring-white/5">
                            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-10 h-10">
                                <rect x="2" y="2" width="44" height="44" rx="14" fill="white"/>
                                <path d="M12 28 Q18 16 24 22 Q30 16 36 28" stroke="#00b386" strokeWidth="5.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                            </svg>
                        </div>
                        <h1 className="text-2xl font-bold text-white mb-1">Wali Admin</h1>
                        <p className="text-slate-400 text-sm">Portail de gestion sécurisé</p>
                    </div>

                    {/* Error Alert */}
                    {error && (
                        <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2">
                            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}

                    <form onSubmit={handleLogin} className="space-y-5">
                        {/* Email Field */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Email professionnel
                            </label>
                            <div className="relative">
                                <span className="absolute left-4 top-3.5 text-slate-500">
                                    <Mail className="w-5 h-5" />
                                </span>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-12 pr-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-white placeholder-slate-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                                    placeholder="admin@wali.ci"
                                    required
                                    disabled={loading}
                                />
                            </div>
                        </div>

                        {/* Password Field */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Mot de passe
                            </label>
                            <div className="relative">
                                <span className="absolute left-4 top-3.5 text-slate-500">
                                    <Lock className="w-5 h-5" />
                                </span>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-12 pr-12 py-3 bg-slate-950 border border-slate-700 rounded-xl text-white placeholder-slate-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                                    placeholder="••••••••"
                                    required
                                    disabled={loading}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-3.5 text-slate-500 hover:text-slate-300 transition"
                                    tabIndex={-1}
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-600/50 text-white font-medium rounded-xl transition shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:cursor-not-allowed mt-2"
                        >
                            {loading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Connexion...
                                </>
                            ) : (
                                <>
                                    <ShieldCheck className="w-5 h-5" />
                                    Se connecter
                                </>
                            )}
                        </button>
                    </form>

                    {/* Footer */}
                    <div className="mt-8 text-center space-y-2">
                        <p className="text-xs text-slate-500">
                            Accès réservé au personnel autorisé uniquement.
                        </p>
                        <p className="text-xs text-slate-600">
                            Toutes les activités sont enregistrées et tracées.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
