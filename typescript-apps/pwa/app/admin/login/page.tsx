'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LayoutDashboard, Lock, Eye, EyeOff, ShieldCheck, HelpCircle, ArrowLeft, Mail, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminLoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [showForgotPassword, setShowForgotPassword] = useState(false);
    const [forgotPasswordStep, setForgotPasswordStep] = useState(1); // 1: email, 2: success
    const [forgotPasswordEmail, setForgotPasswordEmail] = useState('');
    const [forgotPasswordLoading, setForgotPasswordLoading] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        // Simulate admin login delay
        setTimeout(() => {
            if (email === 'admin@wali.com' && (password === 'admin123' || password === 'admin1234')) {
                toast.success('Bienvenue, Administrateur');
                router.push('/admin/claims');
            } else {
                toast.error('Identifiants incorrects');
                setLoading(false);
            }
        }, 1500);
    };

    const handleForgotPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setForgotPasswordLoading(true);

        // Simulate password reset request
        setTimeout(() => {
            setForgotPasswordLoading(false);
            setForgotPasswordStep(2);
            toast.success('Instructions envoyées à votre email');
        }, 1500);
    };

    const resetForgotPassword = () => {
        setShowForgotPassword(false);
        setForgotPasswordStep(1);
        setForgotPasswordEmail('');
    };

    // If showing forgot password flow
    if (showForgotPassword) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                {/* Background elements */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-0 left-1/4 w-full max-w-lg h-full max-h-lg bg-emerald-900/10 rounded-full blur-3xl transform -translate-y-1/2"></div>
                    <div className="absolute bottom-0 right-1/4 w-full max-w-lg h-full max-h-lg bg-blue-900/10 rounded-full blur-3xl transform translate-y-1/2"></div>
                </div>

                <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl relative overflow-hidden">
                    {/* Top decorative bar */}
                    <div className="h-1 bg-gradient-to-r from-emerald-500 to-blue-500 w-full"></div>

                    <div className="p-8">
                        {/* Back button */}
                        <button
                            onClick={resetForgotPassword}
                            className="flex items-center gap-2 text-slate-400 hover:text-white transition mb-6"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            <span className="text-sm">Retour à la connexion</span>
                        </button>

                        <div className="text-center mb-8">
                            <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-inner ring-1 ring-white/5">
                                <Mail className="w-8 h-8 text-emerald-500" />
                            </div>
                            <h1 className="text-2xl font-bold text-white mb-2">
                                {forgotPasswordStep === 1 ? 'Mot de passe oublié' : 'Email envoyé'}
                            </h1>
                            <p className="text-slate-400 text-sm">
                                {forgotPasswordStep === 1 
                                    ? 'Entrez votre email pour réinitialiser votre mot de passe'
                                    : 'Vérifiez votre boîte de réception'
                                }
                            </p>
                        </div>

                        {forgotPasswordStep === 1 ? (
                            <form onSubmit={handleForgotPassword} className="space-y-5">
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Email professionnel
                                    </label>
                                    <div className="relative">
                                        <span className="absolute left-4 top-3.5 text-slate-500">
                                            <LayoutDashboard className="w-5 h-5" />
                                        </span>
                                        <input
                                            type="email"
                                            value={forgotPasswordEmail}
                                            onChange={(e) => setForgotPasswordEmail(e.target.value)}
                                            className="w-full pl-12 pr-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-white placeholder-slate-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                                            placeholder="admin@wali.com"
                                            required
                                            autoFocus
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={forgotPasswordLoading}
                                    className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl transition shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                                >
                                    {forgotPasswordLoading ? (
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    ) : (
                                        <>
                                            <RefreshCw className="w-5 h-5" />
                                            Envoyer les instructions
                                        </>
                                    )}
                                </button>

                                {/* Help note */}
                                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                                    <div className="flex items-start gap-3">
                                        <HelpCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                                        <div className="text-sm text-slate-400">
                                            <p className="mb-2">Vous n'avez pas accès à votre email ?</p>
                                            <a 
                                                href="mailto:support@wali.ci?subject=Urgent%20-%20Réinitialisation%20mot%20de%20passe%20admin" 
                                                className="text-emerald-500 hover:text-emerald-400 font-medium"
                                            >
                                                Contacter le support technique →
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        ) : (
                            /* Success State */
                            <div className="text-center space-y-6">
                                <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto">
                                    <svg className="w-10 h-10 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                </div>
                                
                                <div className="space-y-2">
                                    <p className="text-slate-300">
                                        Nous avons envoyé un email à <strong className="text-white">{forgotPasswordEmail}</strong>
                                    </p>
                                    <p className="text-sm text-slate-500">
                                        Cliquez sur le lien dans l'email pour réinitialiser votre mot de passe. Le lien expire dans 24 heures.
                                    </p>
                                </div>

                                <div className="pt-4 space-y-3">
                                    <button
                                        onClick={() => setForgotPasswordStep(1)}
                                        className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl transition"
                                    >
                                        Renvoyer l'email
                                    </button>
                                    
                                    <button
                                        onClick={resetForgotPassword}
                                        className="w-full py-3 text-emerald-500 hover:text-emerald-400 font-medium transition"
                                    >
                                        Retour à la connexion
                                    </button>
                                </div>

                                {/* Check spam note */}
                                <p className="text-xs text-slate-600">
                                    Vous ne voyez pas l'email ? Vérifiez votre dossier spam ou{' '}
                                    <a href="mailto:support@wali.ci" className="text-slate-400 hover:text-slate-300 underline">
                                        contactez le support
                                    </a>
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    // Normal login form
    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
            {/* Background elements */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-1/4 w-full max-w-lg h-full max-h-lg bg-emerald-900/10 rounded-full blur-3xl transform -translate-y-1/2"></div>
                <div className="absolute bottom-0 right-1/4 w-full max-w-lg h-full max-h-lg bg-blue-900/10 rounded-full blur-3xl transform translate-y-1/2"></div>
            </div>

            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl relative overflow-hidden">
                {/* Top decorative bar */}
                <div className="h-1 bg-gradient-to-r from-emerald-500 to-blue-500 w-full"></div>

                <div className="p-8">
                    <div className="text-center mb-8">
                        <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-inner ring-1 ring-white/5">
                            <ShieldCheck className="w-8 h-8 text-emerald-500" />
                        </div>
                        <h1 className="text-2xl font-bold text-white mb-2">Wali Admin</h1>
                        <p className="text-slate-400 text-sm">Portail de gestion sécurisé</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Email professionnel
                            </label>
                            <div className="relative">
                                <span className="absolute left-4 top-3.5 text-slate-500">
                                    <LayoutDashboard className="w-5 h-5" />
                                </span>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-12 pr-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-white placeholder-slate-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                                    placeholder="admin@wali.com"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label className="block text-sm font-medium text-slate-300">
                                    Mot de passe
                                </label>
                            </div>
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
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-3.5 text-slate-500 hover:text-slate-300 transition"
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        {/* ===== HIGHLY VISIBLE FORGOT PASSWORD LINK ===== */}
                        <div className="flex justify-end">
                            <button
                                type="button"
                                onClick={() => setShowForgotPassword(true)}
                                className="text-sm text-blue-400 hover:text-blue-300 font-medium transition flex items-center gap-1"
                            >
                                <HelpCircle className="w-4 h-4" />
                                Mot de passe oublié ?
                            </button>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl transition shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                'Se connecter'
                            )}
                        </button>
                    </form>

                    {/* ===== HELP SECTION ===== */}
                    <div className="mt-6 pt-6 border-t border-slate-800">
                        <div className="flex items-start gap-3 p-4 bg-slate-800/30 rounded-xl">
                            <HelpCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                            <div className="text-sm">
                                <p className="text-slate-300 mb-1">Problème de connexion ?</p>
                                <p className="text-slate-500">
                                    Contactez le{' '}
                                    <a 
                                        href="mailto:support@wali.ci?subject=Problème%20connexion%20admin" 
                                        className="text-emerald-500 hover:text-emerald-400 font-medium"
                                    >
                                        support technique
                                    </a>
                                    {' '}ou appelez le +225 XX XX XX XX
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="mt-6 text-center">
                        <p className="text-xs text-slate-500">
                            Accès réservé au personnel autorisé uniquement.
                            <br />
                            Toutes les activités sont enregistrées.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
