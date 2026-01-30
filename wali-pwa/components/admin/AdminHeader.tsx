"use client";

import React from 'react';
import { Search, Bell, LogOut } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

interface AdminHeaderProps {
    title: string;
    description: string;
    counts?: { issues: number };
    searchQuery?: string;
    onSearch?: (query: string) => void;
}

export default function AdminHeader({ title, description, counts, searchQuery, onSearch }: AdminHeaderProps) {
    const router = useRouter();

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        toast.success("Déconnecté");
        router.push('/admin');
    };

    return (
        <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 mb-12">
            <div>
                <h1 className="text-4xl font-black text-white mb-2 tracking-tight">{title}</h1>
                <p className="text-slate-400 text-lg font-medium opacity-80">{description}</p>
            </div>

            <div className="flex items-center gap-6">
                <div className="flex items-center gap-3 bg-[#111827] border border-slate-700/50 rounded-xl px-6 py-3 shadow-inner">
                    <Search className="text-slate-500" size={18} />
                    <input
                        type="text"
                        placeholder="Recherche globale..."
                        value={searchQuery || ''}
                        onChange={(e) => onSearch?.(e.target.value)}
                        className="bg-transparent border-none outline-none text-sm text-slate-200 w-64 placeholder:text-slate-600 font-medium"
                    />
                </div>

                <button className="relative p-3 bg-[#111827] border border-slate-700/50 rounded-xl text-slate-400 hover:text-[#0ea5e9] hover:border-[#0ea5e9]/30 transition-all group">
                    <Bell size={20} />
                    {counts && counts.issues > 0 && (
                        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-black w-5 h-5 flex items-center justify-center rounded-lg ring-4 ring-[#0f172a] animate-bounce">
                            {counts.issues}
                        </span>
                    )}
                </button>

                <div className="flex items-center gap-4 pl-6 border-l border-slate-800">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-bold text-white tracking-tight">Admin Wali</p>
                        <p className="text-[10px] font-black text-[#0ea5e9] uppercase tracking-widest opacity-80">Super User</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="p-3 bg-[#111827] border border-slate-700/50 rounded-xl text-slate-400 hover:text-red-400 hover:border-red-400/30 transition-all group"
                        title="Logout"
                    >
                        <LogOut size={20} />
                    </button>
                </div>
            </div>
        </header>
    );
}
