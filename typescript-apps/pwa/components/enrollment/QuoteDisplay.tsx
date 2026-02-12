'use client';

import React from 'react';
import { Check, Shield } from 'lucide-react';

interface QuoteDisplayProps {
    partner: string;
    amount: number;
    productName: string;
    validity?: string;
    onConfirm: () => void;
    onCancel: () => void;
    loading?: boolean;
}

export const QuoteDisplay: React.FC<QuoteDisplayProps> = ({
    partner,
    amount,
    productName,
    onConfirm,
    onCancel,
    loading
}) => {
    return (
        <div className="space-y-6">
            <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
                    <Shield className="w-8 h-8 text-blue-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Offre {partner}
                </h2>
                <p className="text-gray-500 dark:text-gray-400">
                    Basée sur votre profil de risque
                </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-200 dark:border-slate-700 relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-bl-xl">
                    RECOMMANDÉ
                </div>

                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{productName}</h3>
                        <p className="text-sm text-gray-500">Protection complète</p>
                    </div>
                </div>

                <div className="flex items-baseline mb-6">
                    <span className="text-4xl font-extrabold text-gray-900 dark:text-white">
                        {amount.toLocaleString()}
                    </span>
                    <span className="text-xl text-gray-500 ml-2">FCFA</span>
                    <span className="text-sm text-gray-400 ml-2">/ mois</span>
                </div>

                <ul className="space-y-3 mb-8">
                    {['Couverture Santé 80%', 'Indemnité Accident', 'Perte de Revenus'].map((feature, i) => (
                        <li key={i} className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
                            <div className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center flex-shrink-0">
                                <Check className="w-3 h-3 text-emerald-600" />
                            </div>
                            {feature}
                        </li>
                    ))}
                </ul>

                <button
                    onClick={onConfirm}
                    disabled={loading}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-xl py-3.5 font-semibold shadow-lg shadow-blue-500/30 transition-all disabled:opacity-70 flex items-center justify-center gap-2"
                >
                    {loading ? (
                        <span className="animate-spin w-5 h-5 border-2 border-white/30 border-t-white rounded-full" />
                    ) : (
                        'Accepter et Payer'
                    )}
                </button>

                <button
                    onClick={onCancel}
                    className="w-full mt-3 text-gray-500 hover:text-gray-700 dark:text-gray-400 py-2 text-sm font-medium"
                >
                    Refuser l'offre
                </button>
            </div>
        </div>
    );
};
