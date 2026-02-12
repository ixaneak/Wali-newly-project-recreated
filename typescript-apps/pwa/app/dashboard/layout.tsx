"use client";

import BottomNav from '@/components/mobile/BottomNav';
import { Toaster } from 'sonner';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#111827' }}>
            <div style={{ maxWidth: 448, margin: '0 auto', minHeight: '100vh', backgroundColor: '#111827', position: 'relative', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}>
                {children}
                <BottomNav />
            </div>
            <Toaster position="top-center" />
        </div>
    );
}
