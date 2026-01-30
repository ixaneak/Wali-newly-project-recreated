"use client";

import React, { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Shield, Star, ShieldCheck, Users, Check, ArrowLeft, Wrench, Hospital, TrendingUp, Package, Loader2 } from 'lucide-react';
import { PLAN_CONFIG, PlanTier } from '../../types/plans';

const IconComponent = {
    Star: Star,
    Shield: Shield,
    ShieldCheck: ShieldCheck,
    Users: Users
};

const CoverageIcon = {
    Tool: Wrench,
    Hospital: Hospital,
    TrendingUp: TrendingUp,
    Package: Package,
    Users: Users,
    ShieldCheck: ShieldCheck
};

function PlanDetailsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const tier = (searchParams.get('tier') as PlanTier) || 'demarrage';
    const plan = PLAN_CONFIG[tier] || PLAN_CONFIG['demarrage'] || Object.values(PLAN_CONFIG)[0];

    const Icon = plan?.icon ? IconComponent[plan.icon as keyof typeof IconComponent] : null;

    if (!plan) return <div className="p-6 text-center">Plan not found</div>;

    return (
        <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-slate-950 pb-20">
            {/* Header with Gradient */}
            <div className={`relative pt-12 pb-8 px-6 bg-gradient-to-br ${plan.bgGradient} rounded-b-[2.5rem] shadow-sm`}>
                <button
                    onClick={() => router.back()}
                    className="absolute top-4 left-4 p-2 bg-white/50 dark:bg-black/20 rounded-full hover:bg-white/80 transition"
                >
                    <ArrowLeft size={20} className="text-gray-700 dark:text-white" />
                </button>

                <div className="flex flex-col items-center text-center">
                    <div className={`w-20 h-20 rounded-2xl flex items-center justify-center mb-4 bg-white/60 dark:bg-black/20 ${plan.color} shadow-sm backdrop-blur-sm`}>
                        {Icon && <Icon size={40} strokeWidth={2} />}
                    </div>

                    <h1 className={`text-2xl font-bold mb-1 ${plan.color}`}>
                        {plan.nameFr}
                    </h1>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-4 opacity-90">
                        {plan.description}
                    </p>

                    <div className="bg-white/60 dark:bg-black/20 backdrop-blur-sm px-4 py-2 rounded-xl">
                        <span className="text-xl font-bold text-gray-900 dark:text-white">
                            {plan.monthlyPremium.toLocaleString()} <span className="text-sm font-normal text-gray-600 dark:text-gray-400">XOF/mois</span>
                        </span>
                    </div>
                </div>
            </div>

            {/* Content Section */}
            <div className="flex-1 px-6 py-8">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Ce qui est couvert</h3>

                <div className="space-y-3">
                    {tier === 'demarrage' && (
                        <>
                            <CoverageItem icon="Tool" title="Matériel & Équipement" text="Jusqu'à 100,000 XOF" color="text-amber-600" bg="bg-amber-100" />
                            <CoverageItem icon="Hospital" title="Urgence Santé" text="Forfait 25,000 XOF" color="text-red-600" bg="bg-red-100" />
                            <CoverageItem icon="TrendingUp" title="Perte de Revenus" text="5,000 XOF / jour (max 3j)" color="text-blue-600" bg="bg-blue-100" />
                        </>
                    )}

                    {tier === 'classique' && (
                        <>
                            <CoverageItem icon="Tool" title="Matériel & Stock" text="Jusqu'à 500,000 XOF" color="text-emerald-600" bg="bg-emerald-100" />
                            <CoverageItem icon="Hospital" title="Hospitalisation" text="Jusqu'à 100,000 XOF" color="text-red-600" bg="bg-red-100" />
                            <CoverageItem icon="Users" title="Responsabilité Civile" text="Jusqu'à 1,000,000 XOF" color="text-purple-600" bg="bg-purple-100" />
                            <CoverageItem icon="Package" title="Vol de Marchandise" text="Jusqu'à 300,000 XOF" color="text-orange-600" bg="bg-orange-100" />
                        </>
                    )}

                    {(tier === 'pro' || tier === 'cooperative') && (
                        <>
                            <CoverageItem icon="ShieldCheck" title="Couverture Totale" text="Jusqu'à 5,000,000 XOF" color="text-teal-600" bg="bg-teal-100" />
                            <CoverageItem icon="Users" title="Employés & Famille" text="Inclus" color="text-blue-600" bg="bg-blue-100" />
                            <CoverageItem icon="Package" title="Assurance Bâtiment" text="Inclus" color="text-orange-600" bg="bg-orange-100" />
                        </>
                    )}
                </div>

                {/* Upgrade / Downgrade Actions */}
                <div className="mt-8 space-y-3">
                    {tier !== 'pro' && (
                        <button
                            onClick={() => router.push(`/dashboard/upgrade?from=${tier}`)}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-200 dark:shadow-none transition flex items-center justify-center gap-2"
                        >
                            <Star className="w-4 h-4" />
                            Upgrader mon plan
                        </button>
                    )}

                    <button className="w-full bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 text-gray-700 dark:text-gray-300 font-medium py-3.5 rounded-xl hover:bg-gray-50 dark:hover:bg-slate-800 transition">
                        Voir historique de paiements
                    </button>
                </div>
            </div>
        </div>
    );
}

// Wrapper for Suspense boundary
export default function PlanDetails() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-emerald-600" /></div>}>
            <PlanDetailsContent />
        </Suspense>
    );
}

function CoverageItem({ icon, title, text, color, bg }: { icon: keyof typeof CoverageIcon, title: string, text: string, color: string, bg: string }) {
    const Icon = CoverageIcon[icon] || Check;

    return (
        <div className="flex items-center p-3 bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-800 shadow-sm">
            <div className={`p-2.5 rounded-lg mr-3 ${bg} dark:bg-opacity-20`}>
                <Icon size={20} className={color} />
            </div>
            <div>
                <h4 className="font-semibold text-gray-900 dark:text-white text-sm">{title}</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">{text}</p>
            </div>
        </div>
    );
}
