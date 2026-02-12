"use client";

import { useState } from 'react';
import { Shield, ChevronRight } from 'lucide-react';

interface PartnerDisclosureProps {
    onAccept: () => void;
    onDecline?: () => void;
}

export default function PartnerDisclosure({ onAccept, onDecline }: PartnerDisclosureProps) {
    const [accepted, setAccepted] = useState(false);

    return (
        <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl shadow-xl max-w-md mx-auto">
            <div className="text-center mb-6">
                <div className="w-16 h-16 bg-blue-50 dark:bg-blue-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Shield className="w-8 h-8 text-blue-600 dark:text-blue-500" />
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    Information Importante
                </h2>
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                    Pour continuer, vous devez comprendre qui assure votre couverture.
                </p>
            </div>

            <div className="space-y-4 mb-8">
                <div className="bg-gray-50 dark:bg-slate-800 p-4 rounded-xl border border-gray-100 dark:border-slate-700">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-200 mb-1">
                        L'Assureur : NSIA Assurance
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        Souscrit votre contrat, gère les risques et paie les sinistres.
                        <br />
                        <span className="text-xs text-gray-500">(License CIMA N°12345)</span>
                    </p>
                </div>

                <div className="bg-emerald-50 dark:bg-emerald-900/20 p-4 rounded-xl border border-emerald-100 dark:border-emerald-800">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-200 mb-1">
                        La Plateforme : Wali
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        Fournit la technologie pour l'adhésion et la gestion simple de votre dossier.
                    </p>
                </div>
            </div>

            <label className="flex items-start gap-3 p-4 border-2 border-gray-100 dark:border-slate-800 rounded-xl cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800 transition mb-6">
                <div className="relative flex items-center">
                    <input
                        type="checkbox"
                        className="w-5 h-5 border-2 border-gray-300 rounded text-emerald-600 focus:ring-emerald-500 transition"
                        checked={accepted}
                        onChange={(e) => setAccepted(e.target.checked)}
                    />
                </div>
                <span className="text-sm text-gray-700 dark:text-gray-300 font-medium select-none">
                    Je comprends que ma couverture est fournie par NSIA Assurance et que Wali est mon interface technologique.
                </span>
            </label>

            <button
                onClick={onAccept}
                disabled={!accepted}
                className="w-full h-14 bg-emerald-600 text-white rounded-xl font-bold text-lg hover:bg-emerald-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
                Continuer
                <ChevronRight className="w-5 h-5" />
            </button>

            {onDecline && (
                <button
                    onClick={onDecline}
                    className="w-full mt-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 font-medium"
                >
                    Refuser et Retourner
                </button>
            )}
        </div>
    );
}
