'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Building2, Lock, Mail, Users, ArrowRight, CheckCircle2 } from 'lucide-react';
import { pharmacyService } from '@/lib/api-client';
import { toast } from 'sonner';

export default function PharmacyLoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    // For MVP Demo: Auto-fill helper
    const handleDemoFill = () => {
        setEmail('pharmacie@wali.com');
        setPassword('pharma1234');
    };

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        console.log('🔔 Login Submit');
        setLoading(true);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

            const res = await fetch('/api/v1/pharmacy/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ email, password }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // Handle non-JSON responses (HTML errors) or empty bodies
            let data;
            const contentType = res.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                try {
                    data = await res.json();
                } catch (jsonErr) {
                    console.error('Failed to parse JSON:', jsonErr);
                    data = { detail: "Erreur de format de réponse" };
                }
            } else {
                const text = await res.text();
                data = { detail: `Server error: ${text.substring(0, 100)}` };
            }

            if (!res.ok) {
                console.error('Login failed:', data);
                // Safe error extraction
                const errorMsg = data?.detail || data?.error || `Erreur ${res.status}`;
                toast.error(errorMsg);
                return;
            }

            // Success
            console.log('Login success:', data);
            localStorage.setItem('pharmacy_token', data.access_token);
            localStorage.setItem('pharmacy_api_key', data.api_key);
            localStorage.setItem('user_role', 'pharmacy');

            toast.success(`Bienvenue, ${data.business_name}`);

            if (data.subscription_status === 'trial_ended' || data.subscription_status === 'suspended') {
                window.location.href = '/pharmacy/billing';
            } else {
                window.location.href = '/pharmacy';
            }

        } catch (err: any) {
            console.error('Network Error:', err);
            if (err.name === 'AbortError') {
                toast.error('Délai d\'attente dépassé (Timeout).');
            } else {
                toast.error("Erreur réseau: " + err.message);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex">
            {/* Left Side - Brand/Marketing */}
            <div className="hidden lg:flex w-1/2 bg-slate-900 relative overflow-hidden flex-col justify-between p-12 text-white">
                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1631549916768-4119b2e5f926?q=80&w=2938&auto=format&fit=crop')] bg-cover bg-center opacity-20 mix-blend-overlay"></div>
                <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center">
                            <Building2 className="text-white" />
                        </div>
                        <span className="text-2xl font-bold tracking-tight">Wali Pro</span>
                    </div>
                    <h1 className="text-5xl font-bold leading-tight mb-6">
                        La solution SaaS pour les Pharmacies modernes.
                    </h1>
                    <p className="text-slate-300 text-lg max-w-md">
                        Vérifiez la couverture santé de vos clients artisans en temps réel et simplifiez vos remboursements avec NSIA.
                    </p>
                </div>

                <div className="relative z-10 space-y-4">
                    <div className="flex items-center gap-3">
                        <CheckCircle2 className="text-emerald-500" />
                        <span>Vérification instantanée (QR & ID)</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <CheckCircle2 className="text-emerald-500" />
                        <span>Remboursements accélérés</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <CheckCircle2 className="text-emerald-500" />
                        <span>Tableau de bord analytique</span>
                    </div>
                </div>
            </div>

            {/* Right Side - Login Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-gray-50 dark:bg-slate-950">
                <div className="w-full max-w-md space-y-8">
                    <div className="text-center lg:text-left">
                        <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Connexion Espace Pro</h2>
                        <p className="mt-2 text-gray-500">Accédez à votre portail pharmacien</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email professionnel</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Mail className="h-5 w-5 text-gray-400" />
                                </div>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 dark:bg-slate-900 dark:border-slate-800 dark:text-white transition"
                                    placeholder="contact@pharmacie.com"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Mot de passe</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-400" />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 dark:bg-slate-900 dark:border-slate-800 dark:text-white transition"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <div className="flex items-center">
                                <input
                                    id="remember-me"
                                    name="remember-me"
                                    type="checkbox"
                                    className="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded"
                                />
                                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900 dark:text-gray-300">
                                    Se souvenir de moi
                                </label>
                            </div>
                            <div className="text-sm">
                                <a href="#" className="font-medium text-emerald-600 hover:text-emerald-500">
                                    Mot de passe oublié ?
                                </a>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition disabled:opacity-50 disabled:cursor-not-allowed items-center gap-2"
                        >
                            {loading ? 'Connexion...' : 'Se connecter'}
                            {!loading && <ArrowRight className="w-5 h-5" />}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-gray-500">Pour la démo</p>
                        <button
                            type="button"
                            onClick={handleDemoFill}
                            className="text-emerald-600 text-sm font-medium hover:underline"
                        >
                            Remplir avec identifiants démo
                        </button>
                    </div>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-300 dark:border-slate-800"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-2 bg-gray-50 dark:bg-slate-950 text-gray-500">
                                Vous êtes artisan ?
                            </span>
                        </div>
                    </div>

                    <button
                        onClick={() => router.push('/login')}
                        className="w-full flex justify-center py-3 px-4 border border-gray-300 dark:border-slate-700 rounded-xl shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-slate-900 hover:bg-gray-50 dark:hover:bg-slate-800 transition items-center gap-2"
                    >
                        <Users className="w-5 h-5" />
                        Connexion Artisan (Mobile)
                    </button>
                </div>
            </div>
        </div>
    );
}
