export type PlanTier = 'demarrage' | 'classique' | 'pro' | 'cooperative';

export interface PlanDetails {
    tier: PlanTier;
    nameFr: string;
    nameEn: string;
    icon: 'Star' | 'Shield' | 'ShieldCheck' | 'Users';
    color: string; // Tailwind color class or hex
    bgGradient: string; // Tailwind classes for gradient
    monthlyPremium: number;
    coverageLimit: number;
    paymentFrequency: 'daily' | 'weekly' | 'monthly';
    description?: string;
}

export const PLAN_CONFIG: Record<PlanTier, Omit<PlanDetails, 'status' | 'renewalDate' | 'nextPaymentDate'>> = {
    demarrage: {
        tier: 'demarrage',
        nameFr: 'Wali Démarrage',
        nameEn: 'Wali Starter',
        icon: 'Star',
        color: 'text-amber-500',
        bgGradient: 'from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20',
        monthlyPremium: 4500,
        coverageLimit: 100000,
        paymentFrequency: 'daily',
        description: 'Pour débuter en toute sécurité'
    },
    classique: {
        tier: 'classique',
        nameFr: 'Wali Classique',
        nameEn: 'Wali Classic',
        icon: 'Shield',
        color: 'text-emerald-500',
        bgGradient: 'from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20',
        monthlyPremium: 15000,
        coverageLimit: 500000,
        paymentFrequency: 'weekly',
        description: 'La couverture essentielle'
    },
    pro: {
        tier: 'pro',
        nameFr: 'Wali Pro',
        nameEn: 'Wali Pro',
        icon: 'ShieldCheck',
        color: 'text-teal-600',
        bgGradient: 'from-teal-50 to-teal-100 dark:from-teal-900/20 dark:to-teal-800/20',
        monthlyPremium: 50000,
        coverageLimit: 5000000,
        paymentFrequency: 'monthly',
        description: 'Protection maximale'
    },
    cooperative: {
        tier: 'cooperative',
        nameFr: 'Wali Coopérative',
        nameEn: 'Wali Cooperative',
        icon: 'Users',
        color: 'text-violet-500',
        bgGradient: 'from-violet-50 to-violet-100 dark:from-violet-900/20 dark:to-violet-800/20',
        monthlyPremium: 10000,
        coverageLimit: 300000,
        paymentFrequency: 'monthly',
        description: 'Pour les groupes'
    }
};

export interface PlanStatus {
    currentTier: PlanTier;
    status: 'active' | 'inactive' | 'expired' | 'pending_payment';
    nextPaymentDate?: string;
    daysRemaining?: number;
    usagePercent?: number; // Added to merge BalanceCard functionality if needed
}
