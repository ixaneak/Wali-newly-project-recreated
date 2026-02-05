"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
    LayoutGrid,
    FileText,
    Users,
    CreditCard,
    ChartLine,
    Settings,
    LogOut
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

const sidebarItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutGrid, href: '/admin/dash' },
    { id: 'claims', label: 'Claims', icon: FileText, href: '/admin/claims' },
    { id: 'users', label: 'Users', icon: Users, href: '/admin/users' },
    { id: 'payments', label: 'Payments', icon: CreditCard, href: '/admin/payments' },
    { id: 'analytics', label: 'Analytics', icon: ChartLine, href: '/admin/analytics' },
    { id: 'settings', label: 'Settings', icon: Settings, href: '/admin/settings' },
];

export default function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        toast.success("Déconnecté avec succès");
        router.push('/admin');
    };

    return (
        <>
            {/* Mobile Toggle Placeholder - Could be implemented with a sheet component */}
            <aside className="fixed left-0 top-0 h-full w-64 bg-[#0f172a] border-r border-slate-800 z-50 hidden md:flex flex-col shadow-2xl shadow-sky-950/20">
                <div className="p-8 pb-10 flex items-center justify-center">
                    <div className="w-16 h-16 rounded-xl bg-[#0ea5e9] flex items-center justify-center shadow-xl shadow-sky-500/20 hover:scale-105 transition-transform cursor-pointer">
                        <span className="text-4xl font-black text-white">W</span>
                    </div>
                </div>

                <nav className="flex-1 px-4 space-y-2">
                    {sidebarItems.map((item) => {
                        const isActive = pathname === item.href;

                        return (
                            <Link
                                key={item.id}
                                href={item.href}
                                className={cn(
                                    "group flex items-center gap-4 px-6 py-4 rounded-xl transition-all relative overflow-hidden",
                                    isActive
                                        ? "bg-[#1e293b] text-[#0ea5e9] shadow-inner"
                                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                                )}
                            >
                                {isActive && (
                                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-[#0ea5e9] rounded-r-full shadow-[0_0_15px_rgba(14,165,233,0.6)]"></div>
                                )}
                                <item.icon size={20} className={cn(
                                    "transition-colors",
                                    isActive ? "text-[#0ea5e9]" : "text-slate-500 group-hover:text-slate-300"
                                )} />
                                <span className="font-bold text-sm tracking-wide uppercase">{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-8">
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-4 px-6 py-4 rounded-xl text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all group"
                    >
                        <LogOut size={20} className="group-hover:rotate-12 transition-transform" />
                        <span className="font-bold text-sm tracking-wide uppercase text-left">Quitter</span>
                    </button>
                    <div className="mt-6 pt-6 border-t border-slate-800/50">
                        <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest text-center">Wali Console v1.0</p>
                    </div>
                </div>
            </aside>
        </>
    );
}
