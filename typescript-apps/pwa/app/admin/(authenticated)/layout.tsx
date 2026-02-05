"use client";

import React from 'react';
import Sidebar from '@/components/admin/Sidebar';

export default function AuthenticatedAdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-[#0f172a] text-slate-200 font-sans relative overflow-x-hidden selection:bg-sky-500/30">
            <Sidebar />
            <main className="relative z-10 md:ml-64 p-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
                {children}
            </main>
        </div>
    );
}
