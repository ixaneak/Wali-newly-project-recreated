'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Loader2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function PharmacyLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Skip check for login page
        if (pathname === '/pharmacy/login') {
            setLoading(false);
            return;
        }

        const checkAuth = () => {
            try {
                const token = localStorage.getItem('pharmacy_token');
                const apiKey = localStorage.getItem('pharmacy_api_key');
                const role = localStorage.getItem('user_role');

                if (!token || !apiKey || role !== 'pharmacy') {
                    console.log('[PharmacyLayout] Auth check failed, redirecting to login');
                    router.replace('/pharmacy/login');
                    return;
                }

                // Check subscription status
                const subStatus = localStorage.getItem('subscription_status');

                // Block access if trial ended or suspended, unless on billing page
                if ((subStatus === 'trial_ended' || subStatus === 'suspended') && !pathname.includes('/billing')) {
                    console.log('[PharmacyLayout] Subscription expired, redirecting to billing');
                    toast.error('Votre abonnement a expiré. Veuillez renouveler.');
                    router.replace('/pharmacy/billing');
                    return;
                }

                setLoading(false);
            } catch (err) {
                console.error('[PharmacyLayout] Auth check error:', err);
                setError('Erreur de vérification d\'authentification');
                setLoading(false);
            }
        };

        checkAuth();
    }, [pathname, router]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-950">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                    <p className="text-gray-500 text-sm">Chargement...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-950 p-6">
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-sm border border-red-200 dark:border-red-800 max-w-md w-full text-center">
                    <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Erreur</h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
                    <button
                        onClick={() => router.push('/pharmacy/login')}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-xl font-medium transition"
                    >
                        Retour à la connexion
                    </button>
                </div>
            </div>
        );
    }

    return <>{children}</>;
}
