"use client";

import React, { Suspense, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle2, XCircle, Loader2, CreditCard, Shield } from 'lucide-react';
import { PLAN_CONFIG, PlanTier } from '../../types/plans';
import { paymentApi as paymentService } from "@/lib/api-client";
import { toast } from 'sonner';

type PaymentStatus = 'confirming' | 'processing' | 'success' | 'error';

function PaymentConfirmationContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const tier = (searchParams.get('tier') as PlanTier) || 'classique';
    const paymentType = searchParams.get('type') || 'upgrade';

    const [status, setStatus] = useState<PaymentStatus>('confirming');
    const [paymentMethod, setPaymentMethod] = useState<'orange' | 'mtn' | 'wave'>('orange');
    const [phoneNumber, setPhoneNumber] = useState('');

    const plan = PLAN_CONFIG[tier] || PLAN_CONFIG['demarrage'] || Object.values(PLAN_CONFIG)[0];

    const handlePayment = async () => {
        setStatus('processing');

        try {
            // Simulate payment initiation
            const response = await paymentService.initiatePayment({
                user_id: "user-123",
                policy_id: `policy-${tier}`,
                amount: plan.monthlyPremium,
                phone: phoneNumber || "+225 07 07 07 07 07",
                provider: paymentMethod
            });

            // Simulate processing delay
            await new Promise(resolve => setTimeout(resolve, 2000));

            setStatus('success');
            toast.success('Paiement réussi !');

            // Redirect after success
            setTimeout(() => {
                router.push('/dashboard');
            }, 3000);

        } catch (error) {
            console.error('Payment error:', error);
            setStatus('error');
            toast.error('Échec du paiement');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center p-6">
            <div className="w-full max-w-md">

                {/* Confirming State */}
                {status === 'confirming' && (
                    <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-lg">
                        <div className={`w-16 h-16 rounded-2xl mx-auto mb-4 bg-gradient-to-br ${plan.bgGradient} flex items-center justify-center`}>
                            <Shield className={`w-8 h-8 ${plan.color}`} />
                        </div>

                        <h2 className="text-xl font-bold text-center text-gray-900 dark:text-white mb-2">
                            Confirmer votre {paymentType === 'upgrade' ? 'upgrade' : 'paiement'}
                        </h2>

                        <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-4 mb-6">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm text-gray-600 dark:text-gray-400">Plan</span>
                                <span className="font-bold text-gray-900 dark:text-white">{plan.nameFr}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-gray-600 dark:text-gray-400">Montant</span>
                                <span className="text-lg font-bold text-emerald-600">{plan.monthlyPremium.toLocaleString()} XOF</span>
                            </div>
                        </div>

                        {/* Payment Method Selection */}
                        <div className="mb-6">
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                                Moyen de paiement
                            </label>
                            <div className="grid grid-cols-3 gap-3">
                                {[
                                    { id: "orange", name: "Orange", color: "bg-orange-500", text: "text-white" },
                                    { id: "mtn", name: "MTN", color: "bg-yellow-400", text: "text-black" },
                                    { id: "wave", name: "Wave", color: "bg-blue-500", text: "text-white" },
                                ].map((p) => (
                                    <button
                                        key={p.id}
                                        onClick={() => setPaymentMethod(p.id as 'orange' | 'mtn' | 'wave')}
                                        className={`relative p-3 rounded-xl border-2 transition flex flex-col items-center gap-1 ${paymentMethod === p.id
                                            ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                                            : 'border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-gray-50 dark:hover:bg-slate-800'
                                            }`}
                                    >
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${p.color} ${p.text} font-bold text-xs`}>
                                            {p.name[0]}
                                        </div>
                                        <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{p.name}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Phone Number */}
                        <div className="mb-6">
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                Numéro de téléphone
                            </label>
                            <input
                                type="tel"
                                value={phoneNumber}
                                onChange={(e) => setPhoneNumber(e.target.value)}
                                placeholder="+225 07 07 07 07 07"
                                className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                            />
                        </div>

                        <button
                            onClick={handlePayment}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-emerald-200 dark:shadow-none transition flex items-center justify-center gap-2"
                        >
                            <CreditCard className="w-5 h-5" />
                            Payer {plan.monthlyPremium.toLocaleString()} XOF
                        </button>

                        <button
                            onClick={() => router.back()}
                            className="w-full mt-3 text-gray-600 dark:text-gray-400 font-medium py-3 hover:text-gray-900 dark:hover:text-white transition"
                        >
                            Annuler
                        </button>
                    </div>
                )}

                {/* Processing State */}
                {status === 'processing' && (
                    <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg text-center">
                        <Loader2 className="w-16 h-16 mx-auto mb-4 text-emerald-600 animate-spin" />
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                            Traitement en cours...
                        </h2>
                        <p className="text-gray-600 dark:text-gray-400">
                            Veuillez valider le paiement sur votre téléphone
                        </p>
                    </div>
                )}

                {/* Success State */}
                {status === 'success' && (
                    <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg text-center">
                        <div className="w-20 h-20 rounded-full bg-emerald-100 dark:bg-emerald-900/30 mx-auto mb-4 flex items-center justify-center">
                            <CheckCircle2 className="w-12 h-12 text-emerald-600" />
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                            Paiement réussi !
                        </h2>
                        <p className="text-gray-600 dark:text-gray-400 mb-6">
                            Votre plan a été mis à jour vers <span className="font-bold text-emerald-600">{plan.nameFr}</span>
                        </p>
                        <div className="text-sm text-gray-500">
                            Redirection vers le tableau de bord...
                        </div>
                    </div>
                )}

                {/* Error State */}
                {status === 'error' && (
                    <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg text-center">
                        <div className="w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/30 mx-auto mb-4 flex items-center justify-center">
                            <XCircle className="w-12 h-12 text-red-600" />
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                            Échec du paiement
                        </h2>
                        <p className="text-gray-600 dark:text-gray-400 mb-6">
                            Le paiement n'a pas pu être traité. Veuillez réessayer.
                        </p>
                        <button
                            onClick={() => setStatus('confirming')}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-xl transition"
                        >
                            Réessayer
                        </button>
                        <button
                            onClick={() => router.back()}
                            className="w-full mt-3 text-gray-600 dark:text-gray-400 font-medium py-3 hover:text-gray-900 dark:hover:text-white transition"
                        >
                            Retour
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function PaymentConfirmationPage() {
    return (
        <Suspense fallback={
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
            </div>
        }>
            <PaymentConfirmationContent />
        </Suspense>
    );
}
