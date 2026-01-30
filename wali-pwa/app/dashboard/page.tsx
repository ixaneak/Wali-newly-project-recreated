"use client";

import { useState } from 'react';
import { Bell, QrCode, Zap } from 'lucide-react';
import BalanceCard from '@/components/mobile/BalanceCard';
import TransactionList from '@/components/mobile/TransactionList';
import RechargeModal from '@/components/payment/RechargeModal';
import HealthTipsCarousel from '@/components/mobile/HealthTipsCarousel';
import PlanCard from '@/components/dashboard/PlanCard';
import { useDashboard } from '@/hooks/useMobileData';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
    const router = useRouter();
    const { data, loading, error } = useDashboard();
    const [isRechargeOpen, setIsRechargeOpen] = useState(false);

    if (loading) {
        return (
            <div className="p-6 space-y-6 animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
                <div className="h-48 bg-gray-200 rounded-3xl"></div>
                <div className="grid grid-cols-2 gap-4">
                    <div className="h-24 bg-gray-200 rounded-2xl"></div>
                    <div className="h-24 bg-gray-200 rounded-2xl"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return <div className="p-6 text-center text-red-500">{error}</div>;
    }

    if (!data) return null;

    return (
        <div className="p-6">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        Bonjour 👋 <br />
                        <span className="text-emerald-700 dark:text-emerald-500">{data.user.name.split(' ')[0]}</span>
                    </h1>
                </div>
                <button
                    onClick={() => router.push('/dashboard/notifications/inbox')}
                    className="relative bg-white dark:bg-slate-900 p-2.5 rounded-full shadow-sm border border-gray-100 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800 transition"
                >
                    <Bell className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                    {data.notifications > 0 && (
                        <span className="absolute top-0 right-0 w-3 h-3 bg-red-500 border-2 border-white dark:border-slate-900 rounded-full"></span>
                    )}
                </button>
            </div>

            {/* Health Tips */}
            <HealthTipsCarousel />

            {/* Plan Card (New) */}
            <PlanCard
                currentTier={data.user.tier}
                status={data.user.planStatus === 'actif' ? 'active' : 'inactive'}
                daysRemaining={12} // mock for now
            />

            {/* Balance Card (Old, kept for Recharge) */}
            {/* Ideally we merge recharge into PlanCard or keep this below */}
            <BalanceCard
                used={data.coverage.used}
                total={data.coverage.total}
                planName={data.user.planName}
                onRecharge={() => setIsRechargeOpen(true)}
            />

            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-4 mb-8">
                <button
                    onClick={() => router.push('/dashboard/card')}
                    className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 flex flex-col items-center justify-center gap-2 hover:bg-gray-50 dark:hover:bg-slate-800 transition group"
                >
                    <div className="bg-emerald-50 dark:bg-emerald-900/30 p-3 rounded-full group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/50 transition">
                        <QrCode className="w-6 h-6 text-emerald-600 dark:text-emerald-500" />
                    </div>
                    <span className="font-semibold text-gray-700 dark:text-gray-200 text-sm">Mon QR Code</span>
                </button>

                <button
                    onClick={() => toast.info("Services d'urgence")}
                    className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 flex flex-col items-center justify-center gap-2 hover:bg-gray-50 dark:hover:bg-slate-800 transition group"
                >
                    <div className="bg-orange-50 dark:bg-orange-900/30 p-3 rounded-full group-hover:bg-orange-100 dark:group-hover:bg-orange-900/50 transition">
                        <Zap className="w-6 h-6 text-orange-500" />
                    </div>
                    <span className="font-semibold text-gray-700 dark:text-gray-200 text-sm">Urgences</span>
                </button>
            </div>

            {/* Recent Transactions */}
            <div className="mb-4 flex items-center justify-between">
                <h3 className="font-bold text-gray-800 dark:text-white">Activité récente</h3>
                <span className="text-xs font-semibold text-emerald-600 cursor-pointer">Voir tout</span>
            </div>

            {/* Recharge Modal */}
            <RechargeModal
                isOpen={isRechargeOpen}
                onClose={() => setIsRechargeOpen(false)}
                userId={data.user.id || "test-user"}
                userPhone={data.user.phone}
            />

            <TransactionList transactions={data.recentTransactions} />
        </div>
    );
}
