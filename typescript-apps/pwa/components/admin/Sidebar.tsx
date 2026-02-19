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
    LogOut,
    Building2,
    Shield,
    Bell
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { adminAuth } from '@/lib/api-client';

const sidebarItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutGrid, href: '/admin/dash' },
    { id: 'claims', label: 'Claims', icon: FileText, href: '/admin/claims' },
    { id: 'users', label: 'Users', icon: Users, href: '/admin/users' },
    { id: 'pharmacies', label: 'Pharmacies', icon: Building2, href: '/admin/pharmacies' },
    { id: 'payments', label: 'Payments', icon: CreditCard, href: '/admin/payments' },
    { id: 'analytics', label: 'Analytics', icon: ChartLine, href: '/admin/analytics' },
    { id: 'compliance', label: 'Compliance', icon: Shield, href: '/admin/compliance' },
    { id: 'notifications', label: 'Notifications', icon: Bell, href: '/admin/notifications' },
    { id: 'settings', label: 'Settings', icon: Settings, href: '/admin/settings' },
];

export default function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();

    const handleLogout = async () => {
        try {
            // Call logout API
            await adminAuth.logout();
        } catch (e) {
            // Ignore errors
        } finally {
            // Clear localStorage
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            localStorage.removeItem('admin_user');
            
            // Clear auth cookie
            document.cookie = 'wali_auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
            
            toast.success("Déconnecté avec succès");
            router.push('/admin');
        }
    };

    return (
        <>
            {/* Mobile Toggle Placeholder - Could be implemented with a sheet component */}
            <aside className="fixed left-0 top-0 h-full w-64 bg-[#0f172a] border-r border-slate-800 z-50 hidden md:flex flex-col shadow-2xl shadow-sky-950/20">
                <div className="p-8 pb-10 flex items-center justify-center">
                    <Link href="/admin/dash" className="w-16 h-16 rounded-xl bg-white flex items-center justify-center shadow-xl shadow-emerald-500/20 hover:scale-105 transition-transform cursor-pointer">
                        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-12 h-12">
                            <rect x="2" y="2" width="44" height="44" rx="14" fill="white"/>
                            <path d="M12 28 Q18 16 24 22 Q30 16 36 28" stroke="#00b386" strokeWidth="5.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                        </svg>
                    </Link>
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
