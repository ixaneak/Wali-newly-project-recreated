"use client";

import React, { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Check, Star, Shield, ShieldCheck, Users, ArrowLeft, Loader2 } from 'lucide-react';
import { PLAN_CONFIG, PlanTier } from '../../types/plans';

const TIERS: PlanTier[] = ['demarrage', 'classique', 'pro', 'cooperative'];

function UpgradeContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const currentTier = (searchParams.get('from') as PlanTier) || 'demarrage';

    // Filter out current and lower tiers
    const currentTierIndex = TIERS.indexOf(currentTier);
    const upgradeOptions = TIERS.filter((t, idx) => idx > currentTierIndex);

    const handleSelect = (tier: PlanTier) => {
        // In a real app, this would trigger a payment/upgrade flow
        router.push(`/dashboard/payment?type=upgrade&tier=${tier}`);
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 p-6 pb-20">
            {/* Header */}
            <div className="flex items-center gap-4 mb-8">
                <button
                    onClick={() => router.back()}
                    className="p-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800 transition"
                >
                    <ArrowLeft size={20} className="text-gray-700 dark:text-gray-300" />
                </button>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">Choisir mon nouveau plan</h1>
            </div>

            {/* Options */}
            <div className="space-y-6">
                {upgradeOptions.length === 0 ? (
                    <div className="text-center py-10">
                        <p className="text-gray-500">Vous êtes déjà sur le meilleur plan !</p>
                    </div>
                ) : (
                    upgradeOptions.map(tier => {
                        const plan = PLAN_CONFIG[tier];
                        const Icon = {
                            demarrage: Star,
                            classique: Shield,
                            pro: ShieldCheck,
                            cooperative: Users
                        }[tier];

                        return (
                            <div
                                key={tier}
                                onClick={() => handleSelect(tier)}
                                className={`relative bg-white dark:bg-slate-900 rounded-2xl p-5 border-2 border-transparent hover:border-emerald-500 transition-all shadow-sm cursor-pointer group overflow-hidden`}
                            >
                                {tier === 'classique' && (
                                    <div className="absolute top-0 right-0 bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-400 text-[10px] font-bold px-3 py-1 rounded-bl-xl">
                                        Recommandé
                                    </div>
                                )}

                                <div className="flex items-start gap-4 mb-4">
                                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-gray-50 dark:bg-slate-800 ${plan.color} group-hover:scale-110 transition`}>
                                        <Icon size={24} />
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-bold text-lg text-gray-900 dark:text-white flex items-center gap-2">
                                            {plan.nameFr}
                                        </h3>
                                        <p className="text-sm text-gray-500 dark:text-gray-400">{plan.description}</p>
                                    </div>
                                </div>

                                <div className="mb-4">
                                    <span className="text-2xl font-bold text-gray-900 dark:text-white">
                                        {plan.monthlyPremium.toLocaleString()}
                                    </span>
                                    <span className="text-sm text-gray-500 font-medium"> XOF / mois</span>
                                </div>

                                <ul className="space-y-2 mb-5">
                                    <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                        <Check size={16} className="text-emerald-500" />
                                        <span>Jusqu'à {plan.coverageLimit.toLocaleString()} XOF de couverture</span>
                                    </li>
                                    {tier === 'classique' && (
                                        <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                            <Check size={16} className="text-emerald-500" />
                                            <span>Protection Stock & Matériel</span>
                                        </li>
                                    )}
                                    {tier === 'pro' && (
                                        <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                            <Check size={16} className="text-emerald-500" />
                                            <span>Couverture Employés incluse</span>
                                        </li>
                                    )}
                                </ul>

                                <button className="w-full py-3 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-bold text-sm group-hover:bg-emerald-600 dark:group-hover:bg-emerald-500 dark:group-hover:text-white transition">
                                    Choisir ce plan
                                </button>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}

export default function UpgradePage() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center"><Loader2 className="w-8 h-8 animate-spin" /></div>}>
            <UpgradeContent />
        </Suspense>
    );
}
