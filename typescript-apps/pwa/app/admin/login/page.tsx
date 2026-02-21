'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AdminLoginRedirect() {
    const router = useRouter();
    
    useEffect(() => {
        // Redirect to the unified /admin page
        router.replace('/admin');
    }, [router]);
    
    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center">
            <div className="text-center">
                <div className="w-8 h-8 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mx-auto mb-4" />
                <p className="text-slate-400">Redirection...</p>
            </div>
        </div>
    );
}
