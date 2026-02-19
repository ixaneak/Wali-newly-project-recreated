"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { QRCodeSVG } from 'qrcode.react';
import { ArrowLeft, ShieldCheck, Copy, Share2, Info, Loader2 } from 'lucide-react';
import { useDashboard } from '@/hooks/useMobileData';
import { apiService } from '@/lib/api-client';
import { toast } from 'sonner';
import { getAuth } from 'firebase/auth';

export default function DigitalCardPage() {
    const router = useRouter();
    const { data } = useDashboard();
    const [flipped, setFlipped] = useState(false);
    const [qrToken, setQrToken] = useState<string | null>(null);
    const [loadingQr, setLoadingQr] = useState(true);

    useEffect(() => {
        const fetchPolicy = async () => {
            try {
                const auth = getAuth();
                const user = auth.currentUser;
                if (!user) return;

                // Fetch real enrollments
                const policies = await apiService.getUserPolicies(user.uid);
                // Find active policy
                const activePolicy = policies.find((p: any) => p.status === 'active' || p.status === 'trial');

                if (activePolicy && activePolicy.qr_token) {
                    setQrToken(activePolicy.qr_token);
                } else if (activePolicy) {
                    // Fallback if no token (shouldn't happen with new backend)
                    setQrToken(activePolicy.subscription_number);
                }
            } catch (e) {
                console.error("Failed to fetch policy for QR", e);
                // toast.error("Impossible de charger le code QR");
            } finally {
                setLoadingQr(false);
            }
        };
        fetchPolicy();
    }, []);

    if (!data) return null;

    const handleCopyId = () => {
        navigator.clipboard.writeText(qrToken || "Unavailable");
        toast.success("ID copié !");
    };

    return (
        <div className="min-h-screen bg-gray-900 pb-20 flex flex-col">
            {/* Header */}
            <div className="p-4 flex items-center justify-between">
                <button
                    onClick={() => router.back()}
                    className="p-2 bg-white/10 hover:bg-white/20 rounded-full text-white transition backdrop-blur-sm"
                >
                    <ArrowLeft className="w-6 h-6" />
                </button>
                <h1 className="text-lg font-bold text-white">Ma Carte Wali</h1>
                <div className="w-10" />
            </div>

            <div className="flex-1 flex flex-col items-center justify-center p-6 -mt-10">

                {/* Card Container (Flip Effect Placeholder) */}
                <div className="w-full max-w-sm perspective-1000" onClick={() => setFlipped(!flipped)}>
                    <div className={`relative w-full aspect-[1.586] transition-all duration-500 transform-style-3d ${flipped ? 'rotate-y-180' : ''}`}>

                        {/* Front Side */}
                        <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-emerald-600 to-teal-800 rounded-3xl shadow-2xl p-6 flex flex-col justify-between text-white backface-hidden border border-white/10">
                            {/* Card Top */}
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="text-emerald-200 text-xs font-bold tracking-widest mb-1">MEMBRE WALI</div>
                                    <div className="font-bold text-xl tracking-wider">8745 9201 4458</div>
                                </div>
                                <ShieldCheck className="w-8 h-8 text-emerald-300" />
                            </div>

                            {/* Card Middle (Custom Pattern) */}
                            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-white/5 rounded-full blur-3xl" />

                            {/* Card Bottom */}
                            <div className="flex justify-between items-end relative z-10">
                                <div>
                                    <div className="text-emerald-200 text-[10px] font-bold uppercase mb-0.5">Assuré</div>
                                    <div className="font-medium text-lg">{data.user.name}</div>
                                </div>
                                <div className="text-right">
                                    <div className="text-emerald-200 text-[10px] font-bold uppercase mb-0.5">Plan</div>
                                    <div className="font-bold bg-white/20 px-2 py-0.5 rounded text-sm backdrop-blur-sm">
                                        {data.user.planName}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Back Side (QR Code) */}
                        <div className="absolute inset-0 w-full h-full bg-white rounded-3xl shadow-2xl p-6 flex flex-col items-center justify-center backface-hidden rotate-y-180 transform">
                            <div className="text-center mb-4">
                                <h3 className="text-gray-900 font-bold text-lg">Code de Vérification</h3>
                                <p className="text-gray-500 text-xs">Présentez ce code en pharmacie</p>
                            </div>

                            <div className="bg-white p-2 rounded-xl border-2 border-gray-100 mb-2 min-h-[166px] flex items-center justify-center">
                                {loadingQr ? (
                                    <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                                ) : qrToken ? (
                                    <QRCodeSVG value={qrToken} size={150} />
                                ) : (
                                    <p className="text-xs text-gray-400">Aucune police active</p>
                                )}
                            </div>

                            <p className="text-[10px] text-gray-400 mt-2 font-mono">
                                REF: {data.user.id.substring(0, 8).toUpperCase()}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Instructions */}
                <div className="mt-8 text-center space-y-4 max-w-xs">
                    <p className="text-gray-400 text-sm flex items-center justify-center gap-2">
                        <Info className="w-4 h-4" />
                        Appuyez sur la carte pour voir le QR code
                    </p>

                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={handleCopyId}
                            className="bg-gray-800 hover:bg-gray-700 text-white py-3 px-4 rounded-xl flex items-center justify-center gap-2 text-sm font-medium transition"
                        >
                            <Copy className="w-4 h-4" />
                            Copier ID
                        </button>
                        <button className="bg-gray-800 hover:bg-gray-700 text-white py-3 px-4 rounded-xl flex items-center justify-center gap-2 text-sm font-medium transition">
                            <Share2 className="w-4 h-4" />
                            Partager
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
}
