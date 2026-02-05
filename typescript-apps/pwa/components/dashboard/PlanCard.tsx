"use client";

import React from 'react';
import { Shield, Star, ShieldCheck, Users, ChevronRight, AlertCircle, Check } from 'lucide-react';
import { PLAN_CONFIG, PlanTier, PlanDetails } from '../../types/plans';
import { useRouter } from 'next/navigation';

interface PlanCardProps {
    currentTier?: PlanTier;
    status?: 'active' | 'inactive' | 'expired' | 'pending_payment';
    nextPaymentDate?: string;
    daysRemaining?: number;
    language?: 'fr' | 'en';
}

const IconComponent = {
    Star: Star,
    Shield: Shield,
    ShieldCheck: ShieldCheck,
    Users: Users
};

export default function PlanCard({
    currentTier = 'demarrage',
    status = 'active',
    nextPaymentDate,
    daysRemaining = 15,
    language = 'fr'
}: PlanCardProps) {
    const router = useRouter();
    const plan = PLAN_CONFIG[currentTier] || PLAN_CONFIG['demarrage'] || Object.values(PLAN_CONFIG)[0];
    const Icon = plan?.icon ? IconComponent[plan.icon as keyof typeof IconComponent] : null;

    const isExpired = status === 'expired';
    const isPending = status === 'pending_payment';

    // Dynamic status text
    const getStatusText = () => {
        if (isExpired) return language === 'fr' ? 'Expiré' : 'Expired';
        if (isPending) return language === 'fr' ? 'Paiement en attente' : 'Payment Pending';
        return language === 'fr' ? 'Actif' : 'Active';
    };

    // Border color based on status
    const borderColorClass = isExpired ? 'border-l-red-500' : isPending ? 'border-l-amber-500' : {
        demarrage: 'border-l-amber-500',
        classique: 'border-l-emerald-500',
        pro: 'border-l-teal-600',
        cooperative: 'border-l-violet-500'
    }[currentTier];

    return (
        <div
            onClick={() => router.push(`/dashboard/plan?tier=${currentTier}`)}
            className={`relative bg-white dark:bg-slate-900 rounded-2xl shadow-sm border-l-4 overflow-hidden cursor-pointer transition-transform active:scale-[0.98] mb-6 ${borderColorClass}`}
        >
            {/* Gradient Background */}
            <div className={`p-4 flex items-center bg-gradient-to-br ${plan.bgGradient}`}>

                {/* Icon */}
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mr-3 bg-white/50 dark:bg-black/10 ${plan.color}`}>
                    {Icon && <Icon size={24} strokeWidth={2.5} />}
                </div>

                {/* Content */}
                <div className="flex-1">
                    <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {language === 'fr' ? 'Mon plan' : 'My plan'}
                    </span>

                    <div className="flex items-center gap-2 mb-1">
                        <h3 className={`text-lg font-bold ${plan.color}`}>
                            {language === 'fr' ? plan.nameFr : plan.nameEn}
                        </h3>
                        {currentTier === 'classique' && (
                            <span className="bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400 text-[10px] font-bold px-1.5 py-0.5 rounded">
                                ★ Popular
                            </span>
                        )}
                    </div>

                    <div className="flex items-center gap-2">
                        {/* Status Badge */}
                        <div className={`px-2 py-0.5 rounded-full border text-[10px] font-bold
                        ${isExpired
                                ? 'bg-red-100 border-red-200 text-red-600 dark:bg-red-900/30 dark:border-red-800'
                                : isPending
                                    ? 'bg-amber-100 border-amber-200 text-amber-600 dark:bg-amber-900/30 dark:border-amber-800'
                                    : 'bg-white/50 border-transparent text-gray-600 dark:bg-black/20 dark:text-gray-300'
                            }
                    `}>
                            {getStatusText()}
                        </div>

                        {/* Warning Days */}
                        {!isExpired && daysRemaining <= 7 && (
                            <div className="flex items-center gap-1 bg-amber-100 dark:bg-amber-900/30 px-2 py-0.5 rounded-full">
                                <AlertCircle size={10} className="text-amber-600" />
                                <span className="text-[10px] font-bold text-amber-700 dark:text-amber-400">
                                    {daysRemaining}j
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Coverage Info for Pro/Coop */}
                    {(currentTier === 'pro' || currentTier === 'cooperative') && (
                        <p className="text-[10px] text-gray-500 mt-1 font-medium">
                            {language === 'fr'
                                ? `Couverture: ${plan.coverageLimit.toLocaleString()} XOF`
                                : `Coverage: ${plan.coverageLimit.toLocaleString()} XOF`
                            }
                        </p>
                    )}
                </div>

                {/* Arrow / Action */}
                <div className="ml-2 flex items-center gap-2">
                    {isPending && (
                        <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                            <span className="text-white text-xs font-bold">!</span>
                        </div>
                    )}
                    <ChevronRight size={20} className="text-gray-400" />
                </div>
            </div>

            {/* Upgrade Banner (Starter Only) */}
            {currentTier === 'demarrage' && status === 'active' && (
                <div className="bg-emerald-50 dark:bg-emerald-900/20 border-t border-emerald-100 dark:border-emerald-900/50 p-3 flex justify-between items-center">
                    <span className="text-xs text-emerald-800 dark:text-emerald-300 font-medium">
                        Passer à Classique pour 3x plus de couverture
                    </span>
                    <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                        Voir <ChevronRight size={12} />
                    </span>
                </div>
            )}
        </div>
    );
}
