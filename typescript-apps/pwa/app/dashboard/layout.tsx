"use client";

import BottomNav from '@/components/mobile/BottomNav';
import { Toaster } from 'sonner';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-20">
            <div className="max-w-md mx-auto min-h-screen bg-gray-50 dark:bg-slate-950 relative shadow-2xl">
                {children}
                <BottomNav />
            </div>
            <Toaster position="top-center" />
        </div>
    );
}
