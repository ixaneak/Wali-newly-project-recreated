'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function PharmacyLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Skip check for login page
        if (pathname === '/pharmacy/login') {
            setLoading(false);
            return;
        }

        const token = localStorage.getItem('pharmacy_token');
        const role = localStorage.getItem('user_role');

        if (!token || role !== 'pharmacy') {
            router.push('/pharmacy/login');
            return;
        }

        // Check subscription status
        const subStatus = localStorage.getItem('subscription_status'); // 'trial', 'active', 'trial_ended', 'suspended'

        // Block access if trial ended, unless on billing page
        if ((subStatus === 'trial_ended' || subStatus === 'suspended') && pathname !== '/pharmacy/billing') {
            router.push('/pharmacy/billing');
            return;
        }

        setLoading(false);
    }, [pathname, router]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-950">
                <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
            </div>
        );
    }

    return <>{children}</>;
}
