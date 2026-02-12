'use client';

import React from 'react';
import { RefreshCw, ExternalLink } from 'lucide-react';

interface PaymentConfirmationProps {
    message: string;
    onCheckStatus: () => void;
    paymentUrl?: string;
}

export const PaymentConfirmation: React.FC<PaymentConfirmationProps> = ({
    message,
    onCheckStatus,
    paymentUrl
}) => {
    return (
        <div className="space-y-8 text-center py-8">
            <div className="w-20 h-20 bg-orange-100 dark:bg-orange-900/20 rounded-full flex items-center justify-center mx-auto animate-pulse">
                <RefreshCw className="w-10 h-10 text-orange-600 dark:text-orange-400 animate-spin" />
            </div>

            <div className="space-y-2">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Paiement en cours
                </h2>
                <p className="text-gray-600 dark:text-gray-300 max-w-xs mx-auto">
                    {message}
                </p>
            </div>

            {paymentUrl && (
                <a
                    href={paymentUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-xl font-medium transition"
                >
                    Ouvrir la page de paiement <ExternalLink size={16} />
                </a>
            )}

            <button
                onClick={onCheckStatus}
                className="w-full bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white rounded-xl py-3.5 font-medium hover:bg-gray-200 dark:hover:bg-slate-700 transition"
            >
                Vérifier le statut
            </button>
        </div>
    );
};
