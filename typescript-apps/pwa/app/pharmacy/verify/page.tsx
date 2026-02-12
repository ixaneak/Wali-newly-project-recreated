'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { pharmacyService } from '@/lib/api-client';
import { CoverageVerificationResult } from '@/types/app';
import { ArrowLeft, Scan, Search, CheckCircle, XCircle, Banknote, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function VerificationPage() {
    const router = useRouter();
    const [step, setStep] = useState<'scan' | 'result'>('scan');
    const [inputCode, setInputCode] = useState('');
    const [verifying, setVerifying] = useState(false);
    const [result, setResult] = useState<CoverageVerificationResult | null>(null);
    const [reimbursementAmount, setReimbursementAmount] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Simulated Scan Handler
    const handleVerify = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!inputCode) return;

        setVerifying(true);
        try {
            // Input format expected: PHONE:TOKEN or just PHONE for testing
            // We split if colon exists, else use input as phone
            const parts = inputCode.split(':');
            const phone = parts[0];
            const token = parts[1] || '';

            const data = await pharmacyService.verifyCoverage(phone, token);
            setResult(data);
            setStep('result');

            if (data.status === 'active') {
                toast.success("Couverture active confirmée");
            } else {
                toast.error("Couverture inactive ou expirée");
            }
        } catch (error) {
            console.error(error);
            toast.error("Erreur de vérification");
        } finally {
            setVerifying(false);
        }
    };

    const handleSubmitReimbursement = async () => {
        if (!result || !reimbursementAmount) return;

        setSubmitting(true);
        try {
            await pharmacyService.submitReimbursement({
                artisan_phone: inputCode.split(':')[0],
                amount: parseFloat(reimbursementAmount),
                medication_code: 'MED-GENERIC'
            });
            toast.success("Demande de remboursement transmise à NSIA");
            setTimeout(() => {
                router.push('/pharmacy');
            }, 1000);
        } catch (error) {
            console.error(error);
            toast.error("Erreur lors de la transmission");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950">
            {/* Header */}
            <div className="bg-white dark:bg-slate-900 p-4 shadow-sm flex items-center gap-4">
                <button onClick={() => router.back()} className="text-gray-500 hover:text-gray-900 dark:text-gray-400">
                    <ArrowLeft />
                </button>
                <h1 className="text-lg font-bold text-gray-900 dark:text-white">Vérification Couverture</h1>
            </div>

            <div className="p-6 max-w-md mx-auto">
                {step === 'scan' ? (
                    <div className="space-y-6">
                        <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 text-center border-2 border-dashed border-gray-300 dark:border-slate-700">
                            <div className="w-20 h-20 bg-gray-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Scan className="w-10 h-10 text-gray-400" />
                            </div>
                            <p className="text-gray-500 mb-4">Scanner le QR Code du client</p>
                            <button className="bg-gray-900 text-white px-6 py-2 rounded-full text-sm font-medium">
                                Activer la caméra (Simulation)
                            </button>
                        </div>

                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-gray-200 dark:border-slate-700"></div>
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-gray-50 dark:bg-slate-950 text-gray-500">ou saisir manuellement</span>
                            </div>
                        </div>

                        <form onSubmit={handleVerify} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Numéro ou ID Couverture
                                </label>
                                <div className="relative">
                                    <input
                                        type="text"
                                        value={inputCode}
                                        onChange={(e) => setInputCode(e.target.value)}
                                        placeholder="Ex: 0707070707"
                                        className="w-full pl-10 pr-4 py-3 rounded-xl border-gray-200 dark:border-slate-800 focus:ring-emerald-500 focus:border-emerald-500 dark:bg-slate-900 dark:text-white"
                                    />
                                    <Search className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
                                </div>
                            </div>
                            <button
                                type="submit"
                                disabled={verifying || !inputCode}
                                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {verifying && <Loader2 className="animate-spin w-5 h-5" />}
                                Vérifier
                            </button>
                        </form>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {/* Result Card */}
                        <div className={`rounded-2xl p-6 border-l-4 shadow-sm ${result?.status === 'active'
                                ? 'bg-white dark:bg-slate-900 border-emerald-500'
                                : 'bg-red-50 dark:bg-red-900/10 border-red-500'
                            }`}>
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                                        {result?.artisan_name}
                                    </h2>
                                    <p className="text-gray-500 text-sm">ID: {result?.coverage_id}</p>
                                </div>
                                {result?.status === 'active' ? (
                                    <CheckCircle className="w-8 h-8 text-emerald-500" />
                                ) : (
                                    <XCircle className="w-8 h-8 text-red-500" />
                                )}
                            </div>

                            <div className="grid grid-cols-2 gap-4 mt-4 py-4 border-t border-gray-100 dark:border-slate-800">
                                <div>
                                    <p className="text-xs text-gray-500 uppercase">Statut</p>
                                    <p className={`font-bold ${result?.status === 'active' ? 'text-emerald-600' : 'text-red-600'
                                        }`}>
                                        {result?.status === 'active' ? 'ACTIF' : 'INACTIF'}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 uppercase">Plafond Remb.</p>
                                    <p className="font-bold text-gray-900 dark:text-white">
                                        {result?.max_reimbursement.toLocaleString()} FCFA
                                    </p>
                                </div>
                            </div>

                            <p className="text-xs text-gray-400 mt-2">Réf. Partenaire: {result?.partner_reference}</p>
                        </div>

                        {/* Action if Active */}
                        {result?.status === 'active' && (
                            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm">
                                <h3 className="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                    <Banknote className="w-5 h-5 text-emerald-600" />
                                    Déclarer une prestation
                                </h3>

                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                            Montant à rembourser (FCFA)
                                        </label>
                                        <input
                                            type="number"
                                            value={reimbursementAmount}
                                            onChange={(e) => setReimbursementAmount(e.target.value)}
                                            placeholder="Ex: 5000"
                                            className="w-full px-4 py-3 rounded-xl border-gray-200 dark:border-slate-800 focus:ring-emerald-500 focus:border-emerald-500 dark:bg-slate-900 dark:text-white"
                                        />
                                    </div>
                                    <button
                                        onClick={handleSubmitReimbursement}
                                        disabled={submitting || !reimbursementAmount}
                                        className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                                    >
                                        {submitting && <Loader2 className="animate-spin w-5 h-5" />}
                                        Transmettre à NSIA
                                    </button>
                                </div>
                            </div>
                        )}

                        <button
                            onClick={() => { setStep('scan'); setInputCode(''); }}
                            className="w-full text-gray-500 font-medium py-2"
                        >
                            Nouvelle vérification
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
