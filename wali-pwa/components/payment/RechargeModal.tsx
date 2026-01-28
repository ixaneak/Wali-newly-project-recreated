"use client";

import { useState } from "react";
import { X, Loader2, Smartphone } from "lucide-react";
import { toast } from "sonner";
import { paymentService } from "@/lib/api-client";

interface RechargeModalProps {
    isOpen: boolean;
    onClose: () => void;
    userId: string; // Needed for payment request
    userPhone: string; // Needed for payment request
}

export default function RechargeModal({ isOpen, onClose, userId, userPhone }: RechargeModalProps) {
    const [amount, setAmount] = useState("5000");
    const [provider, setProvider] = useState("orange"); // orange, mtn, wave
    const [loading, setLoading] = useState(false);

    if (!isOpen) return null;

    const handlePayment = async () => {
        if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) {
            toast.error("Montant invalide");
            return;
        }

        setLoading(true);
        try {
            // Assuming a default policyID for simple recharge or passed via props
            const policyId = "policy-universal";

            await paymentService.initiatePayment({
                user_id: userId || "user-123", // Fallback if not loaded
                policy_id: policyId,
                amount: Number(amount),
                phone: userPhone || "+22500000000",
                provider: provider
            });

            toast.success("Paiement initié avec succès !");
            onClose();
        } catch (error: any) {
            console.error("Payment Error:", error);
            toast.error(error.response?.data?.error || "Erreur lors du paiement");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-white dark:bg-slate-900 w-full max-w-sm rounded-3xl p-6 shadow-xl animate-in slide-in-from-bottom duration-300">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">Recharger</h2>
                    <button onClick={onClose} className="p-2 bg-gray-100 dark:bg-slate-800 rounded-full hover:bg-gray-200 dark:hover:bg-slate-700 transition">
                        <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                    </button>
                </div>

                {/* Amount Input */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Montant (FCFA)</label>
                    <div className="relative">
                        <input
                            type="number"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                            className="w-full bg-gray-50 dark:bg-slate-800 border-none rounded-2xl p-4 text-2xl font-bold text-center text-emerald-600 focus:ring-2 focus:ring-emerald-500 outline-none"
                        />
                    </div>
                </div>

                {/* Provider Selection */}
                <div className="mb-8">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Moyen de paiement</label>
                    <div className="grid grid-cols-3 gap-3">
                        {[
                            { id: "orange", name: "Orange", color: "bg-orange-500", text: "text-white" },
                            { id: "mtn", name: "MTN", color: "bg-yellow-400", text: "text-black" },
                            { id: "wave", name: "Wave", color: "bg-blue-500", text: "text-white" },
                        ].map((p) => (
                            <button
                                key={p.id}
                                onClick={() => setProvider(p.id)}
                                className={`relative p-3 rounded-xl border-2 transition flex flex-col items-center gap-1 ${provider === p.id
                                        ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20"
                                        : "border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-gray-50 dark:hover:bg-slate-800"
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

                {/* Action Button */}
                <button
                    onClick={handlePayment}
                    disabled={loading}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-4 rounded-2xl transition shadow-lg shadow-emerald-200 dark:shadow-none flex items-center justify-center gap-2"
                >
                    {loading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                        <>
                            <Smartphone className="w-5 h-5" />
                            Payer {Number(amount).toLocaleString()} F
                        </>
                    )}
                </button>
            </div>
        </div>
    );
}
