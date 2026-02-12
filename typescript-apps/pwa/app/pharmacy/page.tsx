'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { pharmacyService } from '@/lib/api-client';
import { PharmacyPartner } from '@/types/app';
import { Scan, Activity, Calendar, ShieldCheck, AlertCircle, LogOut } from 'lucide-react';
import { toast } from 'sonner';

export default function PharmacyDashboard() {
    const router = useRouter();
    const [stats, setStats] = useState<PharmacyPartner | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadStats = async () => {
            // In real app, we check if user has 'pharmacy' role here or in middleware
            // For now we rely on the redirect from login
            try {
                const data = await pharmacyService.getStats();
                setStats(data);
            } catch (e) {
                toast.error("Impossible de charger les statistiques");
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        loadStats();
    }, []);

    const handleScan = () => {
        router.push('/pharmacy/verify');
    };

    const handleLogout = () => {
        localStorage.removeItem('pharmacy_token');
        localStorage.removeItem('pharmacy_api_key');
        localStorage.removeItem('user_role');
        localStorage.removeItem('subscription_status');
        localStorage.removeItem('business_name');
        toast.success("Déconnexion réussie");
        router.push('/pharmacy/login');
    };

    if (loading) return <div className="min-h-screen flex items-center justify-center">Chargement...</div>;
    if (!stats) return <div className="min-h-screen flex items-center justify-center">Erreur de chargement.</div>;

    const daysLeft = stats.trial_ends_at
        ? Math.ceil((new Date(stats.trial_ends_at).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
        : 0;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 p-6">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{stats.name}</h1>
                    <p className="text-gray-500">Portail Pharmacie</p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleLogout}
                        className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full transition"
                        title="Se déconnecter"
                    >
                        <LogOut size={20} />
                    </button>
                    <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                        <ShieldCheck className="text-emerald-600" />
                    </div>
                </div>
            </header>

            {/* Subscription Banner */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl p-6 mb-8 text-white relative overflow-hidden">
                <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-2">
                        {stats.subscription_status === 'active' ? (
                            <span className="bg-white/20 px-2 py-1 rounded text-xs font-bold">ABONNEMENT ACTIF</span>
                        ) : (
                            <span className="bg-orange-500/80 px-2 py-1 rounded text-xs font-bold">ESSAI GRATUIT</span>
                        )}
                        <span className="text-sm opacity-80">
                            • {stats.subscription_status === 'trial' ? `${daysLeft} jours restants` : 'Renouvellement le 01/03'}
                        </span>
                    </div>
                    <h2 className="text-3xl font-bold mb-1">50 000 FCFA</h2>
                    <p className="text-blue-100 text-sm">Frais mensuel de plateforme SaaS</p>
                </div>
                <Activity className="absolute right-4 bottom-4 w-24 h-24 text-white/10" />
            </div>

            {/* Main Action */}
            <button
                onClick={handleScan}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl p-6 flex flex-col items-center justify-center gap-3 shadow-lg shadow-emerald-500/20 transition mb-8 group"
            >
                <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center group-hover:scale-110 transition">
                    <Scan className="w-8 h-8" />
                </div>
                <span className="text-xl font-bold">Vérifier une couverture</span>
                <span className="text-emerald-100 text-sm">Scanner le QR Code artisan</span>
            </button>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-gray-100 dark:border-slate-800">
                    <div className="flex items-center gap-2 mb-2 text-gray-500">
                        <Activity size={18} />
                        <span className="text-sm font-medium">Vérifications</span>
                    </div>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.verifications_today}</p>
                    <p className="text-xs text-green-500 mt-1">Aujourd'hui</p>
                </div>

                <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-gray-100 dark:border-slate-800">
                    <div className="flex items-center gap-2 mb-2 text-gray-500">
                        <AlertCircle size={18} />
                        <span className="text-sm font-medium">Quota API</span>
                    </div>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.api_quota_remaining}</p>
                    <p className="text-xs text-gray-400 mt-1">Requêtes restantes</p>
                </div>
            </div>

            <div className="mt-8">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Dernières Activités</h3>
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-gray-100 dark:border-slate-800 text-center text-gray-500 py-8">
                    Aucune activité récente.
                </div>
            </div>
        </div>
    );
}
