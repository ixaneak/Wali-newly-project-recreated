"use client";

import { useEffect, useState } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { Scan, Search, AlertCircle, CheckCircle, XCircle, Loader2, Stethoscope, Plus, X } from 'lucide-react';
import { toast } from 'sonner';
import { claimsService } from '@/lib/api-client';

interface VerificationResult {
    status: string;
    memberId: string;
    name: string;
    plan: string;
    coverageLimit: number;
    copay: number;
    lastPayment: string;
}

export default function PharmacyDashboard() {
    const [scanning, setScanning] = useState(false);
    const [manualId, setManualId] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<VerificationResult | null>(null);

    // Claim Modal State
    const [showClaimModal, setShowClaimModal] = useState(false);
    const [claimLoading, setClaimLoading] = useState(false);
    const [claimData, setClaimData] = useState({
        medication: '',
        amount: '',
        description: ''
    });

    const verifyMember = async (id: string) => {
        setLoading(true);
        setScanning(false);
        setResult(null);

        try {
            const data = await claimsService.verifyCoverage(id);
            if (data.status === 'active') {
                setResult(data as VerificationResult);
                toast.success('Assuré vérifié avec succès');
            } else {
                setResult(data as VerificationResult);
                toast.error('Assuré non trouvé ou inactif');
            }
        } catch (error) {
            toast.error('Erreur de vérification');
        } finally {
            setLoading(false);
        }
    };

    const handleScanSuccess = (decodedText: string) => {
        try {
            const data = JSON.parse(decodedText);
            if (data.uid) verifyMember(data.uid);
        } catch (e) {
            verifyMember(decodedText);
        }
    };

    const handleSubmitClaim = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!result) return;

        setClaimLoading(true);
        try {
            await claimsService.submitClaim({
                claim_type: 'medical', // Using 'medical' but tracking as pharmacy via description
                amount: parseFloat(claimData.amount),
                description: `[PHARMACIE] ${claimData.medication} - ${claimData.description}`,
                incident_date: new Date().toISOString(),
                photos: [], // Optional for now
                policy_id: "POL-2024-001" // Should imply from verification result in real app
            });
            toast.success('Demande de remboursement envoyée !');
            setShowClaimModal(false);
            setClaimData({ medication: '', amount: '', description: '' });
        } catch (e) {
            toast.error("Erreur lors de l'envoi");
            console.error(e);
        } finally {
            setClaimLoading(false);
        }
    };

    useEffect(() => {
        if (scanning) {
            // Give DOM time to render the 'reader' element
            const timeoutId = setTimeout(() => {
                // @ts-ignore
                const scanner = new Html5QrcodeScanner(
                    "reader",
                    { fps: 10, qrbox: { width: 250, height: 250 } },
                    false
                );

                scanner.render(
                    handleScanSuccess,
                    (err) => {
                        // Ignore standard scanning errors to avoid console spam
                        if (typeof err === "string" && !err.includes("NotFound")) {
                            console.log(err);
                        }
                    }
                );

                // Store in window or ref if needed to clear properly, but simpler logic here:
                // Use a cleanup function that handles the clear promise
                return () => {
                    scanner.clear().catch(err => console.error("Failed to clear scanner", err));
                };
            }, 100);

            return () => clearTimeout(timeoutId);
        }
    }, [scanning]);

    return (
        <div className="space-y-6 relative">
            {/* Action Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 md:p-8">
                <h2 className="text-xl font-bold text-gray-900 mb-6">Vérification de Couverture</h2>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* Scanner Section */}
                    <div className="space-y-4">
                        <div className="bg-slate-50 rounded-xl border-2 border-dashed border-gray-300 p-8 text-center min-h-[300px] flex flex-col items-center justify-center relative overflow-hidden">
                            {scanning ? (
                                <div id="reader" className="w-full"></div>
                            ) : (
                                <>
                                    <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-4">
                                        <Scan className="w-8 h-8" />
                                    </div>
                                    <h3 className="font-semibold text-gray-900">Scanner le QR Code</h3>
                                    <p className="text-sm text-gray-500 mb-6 max-w-xs mx-auto">
                                        Placez le QR code du client devant la caméra pour vérifier instantanément sa couverture.
                                    </p>
                                    <button
                                        onClick={() => setScanning(true)}
                                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg font-medium transition shadow-lg shadow-emerald-200"
                                    >
                                        Activer la caméra
                                    </button>
                                </>
                            )}
                            {scanning && (
                                <button
                                    onClick={() => setScanning(false)}
                                    className="absolute top-4 right-4 bg-white/80 p-2 rounded-full text-gray-600 hover:text-red-500"
                                >
                                    <XCircle className="w-6 h-6" />
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Manual Entry Section */}
                    <div className="flex flex-col justify-center space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Recherche manuelle
                            </label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={manualId}
                                    onChange={(e) => setManualId(e.target.value)}
                                    placeholder="Entrez l'ID membre (ex: 8745...)"
                                    className="flex-1 px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition"
                                />
                                <button
                                    onClick={() => verifyMember(manualId)}
                                    disabled={!manualId || loading}
                                    className="px-6 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-medium transition disabled:opacity-50 flex items-center gap-2"
                                >
                                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                                    Vérifier
                                </button>
                            </div>
                        </div>

                        {/* Result Card */}
                        {result && (
                            <div className={`rounded-xl border ${result.status === 'active' ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'} p-6 animate-in slide-in-from-bottom duration-500`}>
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            {result.status === 'active' ? (
                                                <CheckCircle className="w-6 h-6 text-emerald-600" />
                                            ) : (
                                                <AlertCircle className="w-6 h-6 text-red-600" />
                                            )}
                                            <span className={`font-bold text-lg ${result.status === 'active' ? 'text-emerald-800' : 'text-red-800'} uppercase`}>
                                                {result.status === 'active' ? 'Couverture Active' : 'Non Couvert'}
                                            </span>
                                        </div>
                                        <div className="text-sm opacity-80 pl-8">
                                            Dernier paiement : {result.lastPayment}
                                        </div>
                                    </div>
                                    {result.status === 'active' && (
                                        <div className="text-right">
                                            <div className="text-xs text-emerald-600 font-bold uppercase mb-1">Reste à charge</div>
                                            <div className="text-2xl font-bold text-emerald-700">{result.copay}%</div>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-3 pl-8">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <div className="text-xs uppercase tracking-wide opacity-60 mb-0.5">Assuré</div>
                                            <div className="font-semibold">{result.name}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs uppercase tracking-wide opacity-60 mb-0.5">Plan</div>
                                            <div className="font-semibold">{result.plan}</div>
                                        </div>
                                    </div>

                                    {result.status === 'active' && (
                                        <div className="pt-4 border-t border-black/5 mt-4">
                                            <button
                                                onClick={() => setShowClaimModal(true)}
                                                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold shadow-md transition flex items-center justify-center gap-2"
                                            >
                                                <Plus className="w-5 h-5" />
                                                Déclarer un soin / Remboursement
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {!result && !loading && (
                            <div className="text-center text-gray-400 py-8">
                                <Stethoscope className="w-12 h-12 mx-auto mb-2 opacity-20" />
                                <p className="text-sm">En attente de vérification...</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Claim Modal */}
            {showClaimModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden">
                        <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                            <h3 className="font-bold text-lg">Déclarer un soin</h3>
                            <button onClick={() => setShowClaimModal(false)} className="p-1 hover:bg-gray-200 rounded-full">
                                <X className="w-6 h-6 text-gray-500" />
                            </button>
                        </div>

                        <form onSubmit={handleSubmitClaim} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Médicament / Soin</label>
                                <input
                                    type="text"
                                    required
                                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                                    placeholder="Ex: Amoxicilline 500mg"
                                    value={claimData.medication}
                                    onChange={e => setClaimData({ ...claimData, medication: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Coût Total (FCFA)</label>
                                <input
                                    type="number"
                                    required
                                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                                    placeholder="0"
                                    value={claimData.amount}
                                    onChange={e => setClaimData({ ...claimData, amount: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Notes / Posologie</label>
                                <textarea
                                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                                    rows={3}
                                    placeholder="Détails supplémentaires..."
                                    value={claimData.description}
                                    onChange={e => setClaimData({ ...claimData, description: e.target.value })}
                                />
                            </div>

                            <div className="bg-emerald-50 p-4 rounded-lg flex justify-between items-center text-sm font-medium text-emerald-800">
                                <span>Part Patient ({result?.copay}%)</span>
                                <span>{claimData.amount ? (parseFloat(claimData.amount) * (result?.copay || 0) / 100).toLocaleString() : 0} FCFA</span>
                            </div>

                            <div className="pt-2">
                                <button
                                    type="submit"
                                    disabled={claimLoading}
                                    className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold shadow-md transition disabled:opacity-50 flex justify-center gap-2"
                                >
                                    {claimLoading && <Loader2 className="animate-spin w-5 h-5" />}
                                    Soumettre la demande
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
