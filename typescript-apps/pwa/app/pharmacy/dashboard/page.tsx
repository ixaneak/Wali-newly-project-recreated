'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { 
    Scan, 
    History, 
    TrendingUp, 
    Users,
    AlertCircle,
    CheckCircle,
    Clock,
    ArrowRight
} from 'lucide-react';
import { toast } from 'sonner';
import { pharmacyService } from '@/lib/api-client';
import { PharmacyPartner } from '@/types/app';

interface RecentTransaction {
    id: string;
    patientName: string;
    amount: number;
    patientShare: number;
    waliShare: number;
    date: string;
    status: 'completed' | 'pending' | 'failed';
}

export default function PharmacyDashboard() {
    const [stats, setStats] = useState<PharmacyPartner | null>(null);
    const [loading, setLoading] = useState(true);
    const [recentTransactions, setRecentTransactions] = useState<RecentTransaction[]>([]);

    useEffect(() => {
        const loadData = async () => {
            try {
                const statsData = await pharmacyService.getStats();
                setStats(statsData);
                
                // TODO: Load recent transactions from API when available
                // For now, use empty state
                setRecentTransactions([]);
            } catch (e) {
                toast.error("Impossible de charger les statistiques");
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        
        loadData();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
                    <p className="text-gray-500">Chargement...</p>
                </div>
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="min-h-screen flex items-center justify-center p-6">
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-sm border border-red-200 dark:border-red-800 max-w-md w-full text-center">
                    <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Erreur de chargement</h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">Impossible de charger les statistiques</p>
                </div>
            </div>
        );
    }

    const daysLeft = stats.trial_ends_at
        ? Math.ceil((new Date(stats.trial_ends_at).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
        : 0;

    return (
        <div className="space-y-6">
            {/* Welcome Header */}
            <div className="bg-gradient-to-r from-emerald-600 to-emerald-800 rounded-2xl p-6 text-white">
                <h1 className="text-2xl font-bold mb-2">Bonjour, {stats.name}</h1>
                <p className="text-emerald-100">Bienvenue dans votre portail pharmacien</p>
            </div>

            {/* Main Action */}
            <Link href="/pharmacy/verify">
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-slate-800 hover:shadow-md transition cursor-pointer group">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center group-hover:scale-110 transition">
                                <Scan className="w-7 h-7 text-emerald-600" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Nouvelle vérification</h2>
                                <p className="text-sm text-gray-500">Scanner un QR code ou saisir manuellement</p>
                            </div>
                        </div>
                        <ArrowRight className="w-6 h-6 text-gray-400 group-hover:text-emerald-600 transition" />
                    </div>
                </div>
            </Link>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-gray-100 dark:border-slate-800">
                    <div className="flex items-center gap-2 mb-3 text-gray-500">
                        <CheckCircle size={18} />
                        <span className="text-sm font-medium">Vérifications</span>
                    </div>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.verifications_today}</p>
                    <p className="text-xs text-green-500 mt-1">Aujourd&apos;hui</p>
                </div>

                <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-gray-100 dark:border-slate-800">
                    <div className="flex items-center gap-2 mb-3 text-gray-500">
                        <Users size={18} />
                        <span className="text-sm font-medium">Patients</span>
                    </div>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">-</p>
                    <p className="text-xs text-gray-400 mt-1">Ce mois</p>
                </div>

                <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-gray-100 dark:border-slate-800">
                    <div className="flex items-center gap-2 mb-3 text-gray-500">
                        <TrendingUp size={18} />
                        <span className="text-sm font-medium">Montant</span>
                    </div>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">-</p>
                    <p className="text-xs text-gray-400 mt-1">FCFA remboursés</p>
                </div>

                <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-gray-100 dark:border-slate-800">
                    <div className="flex items-center gap-2 mb-3 text-gray-500">
                        <AlertCircle size={18} />
                        <span className="text-sm font-medium">Quota API</span>
                    </div>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.api_quota_remaining}</p>
                    <p className="text-xs text-gray-400 mt-1">Requêtes restantes</p>
                </div>
            </div>

            {/* Subscription Status */}
            <div className={`rounded-2xl p-5 ${
                stats.subscription_status === 'active' 
                    ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800' 
                    : 'bg-orange-50 dark:bg-orange-900/20 border border-orange-100 dark:border-orange-800'
            }`}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            stats.subscription_status === 'active' ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'
                        }`}>
                            <Clock className="w-5 h-5" />
                        </div>
                        <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                                {stats.subscription_status === 'active' ? 'Abonnement Actif' : 'Essai Gratuit'}
                            </p>
                            <p className="text-sm text-gray-500">
                                {stats.subscription_status === 'trial' 
                                    ? `${daysLeft} jours restants` 
                                    : 'Renouvellement mensuel'}
                            </p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-lg font-bold text-gray-900 dark:text-white">50 000 FCFA</p>
                        <p className="text-xs text-gray-500">par mois</p>
                    </div>
                </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-gray-100 dark:border-slate-800 overflow-hidden">
                <div className="p-5 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <History className="w-5 h-5 text-gray-500" />
                        <h3 className="font-bold text-gray-900 dark:text-white">Activités Récentes</h3>
                    </div>
                </div>
                
                {recentTransactions.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                        <History className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p>Aucune activité récente.</p>
                        <p className="text-sm text-gray-400 mt-1">Les vérifications apparaîtront ici</p>
                    </div>
                ) : (
                    <div className="divide-y divide-gray-100 dark:divide-slate-800">
                        {recentTransactions.map((tx) => (
                            <div key={tx.id} className="p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-slate-800/50 transition">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                                        tx.status === 'completed' ? 'bg-green-100 text-green-600' :
                                        tx.status === 'pending' ? 'bg-yellow-100 text-yellow-600' :
                                        'bg-red-100 text-red-600'
                                    }`}>
                                        {tx.status === 'completed' ? <CheckCircle className="w-5 h-5" /> :
                                         tx.status === 'pending' ? <Clock className="w-5 h-5" /> :
                                         <AlertCircle className="w-5 h-5" />}
                                    </div>
                                    <div>
                                        <p className="font-medium text-gray-900 dark:text-white">{tx.patientName}</p>
                                        <p className="text-sm text-gray-500">{new Date(tx.date).toLocaleString('fr-FR')}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="font-bold text-gray-900 dark:text-white">{tx.amount.toLocaleString()} FCFA</p>
                                    <p className="text-xs text-gray-500">Wali: {tx.waliShare.toLocaleString()} FCFA</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
